import os
import shutil
import subprocess
import datetime
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from django.db import transaction, connection
from django.core.mail import EmailMessage
from settings.models import AdminUser, Business

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Restore database from backup file'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to backup file to restore'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt (use with caution!)'
        )
        parser.add_argument(
            '--email',
            action='store_true',
            help='Send email notification after restore'
        )
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create superuser after restore'
        )

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        confirm = options['confirm']
        send_email = options['email']
        create_superuser = options['create_superuser']

        try:
            # Validate backup file exists
            if not os.path.exists(backup_file):
                raise Exception(f"Backup file not found: {backup_file}")

            # Get database settings
            db_settings = settings.DATABASES['default']
            db_engine = db_settings['ENGINE']

            # Safety confirmation
            if not confirm:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  WARNING: This will COMPLETELY REPLACE your current database!"
                    )
                )
                self.stdout.write(f"Database: {db_settings['NAME']}")
                self.stdout.write(f"Backup file: {backup_file}")
                self.stdout.write(f"File size: {os.path.getsize(backup_file):,} bytes")
                self.stdout.write("")
                
                confirm_input = input("Type 'YES' to continue (anything else to cancel): ")
                if confirm_input != 'YES':
                    self.stdout.write("❌ Restore cancelled")
                    return

            # Create backup of current database before restore
            self.stdout.write("📋 Creating safety backup of current database...")
            safety_backup_dir = os.path.join(
                getattr(settings, 'BACKUP_DIR', os.path.join(settings.BASE_DIR, 'backups')),
                'safety_backups'
            )
            os.makedirs(safety_backup_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            safety_backup_file = os.path.join(safety_backup_dir, f'pre_restore_backup_{timestamp}')
            
            try:
                call_command('simple_backup', type='manual')
                self.stdout.write("✅ Safety backup created")
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Could not create safety backup: {e}")
                )

            # Perform restore based on database type
            self.stdout.write(f"🔄 Restoring database from {backup_file}...")
            
            if 'sqlite' in db_engine:
                success = self.restore_sqlite(backup_file, db_settings)
            elif 'postgresql' in db_engine:
                success = self.restore_postgresql(backup_file, db_settings)
            elif 'mysql' in db_engine:
                success = self.restore_mysql(backup_file, db_settings)
            else:
                raise Exception(f"Unsupported database engine: {db_engine}")

            if success:
                self.stdout.write(
                    self.style.SUCCESS("✅ Database restore completed successfully!")
                )

                # Run migrations to ensure schema is up to date
                self.stdout.write("🔄 Running migrations...")
                call_command('migrate', verbosity=0)
                
                # Preserve superuser accounts - recreate if missing
                self.preserve_superuser_access()

                # Send email notification
                if send_email:
                    self.send_restore_notification(backup_file, True)

                self.stdout.write(
                    self.style.SUCCESS("🎉 Restore process completed!")
                )

            else:
                if send_email:
                    self.send_restore_notification(backup_file, False)

        except Exception as e:
            logger.error(f'Database restore failed: {e}')
            self.stdout.write(self.style.ERROR(f'❌ Restore failed: {e}'))
            
            if send_email:
                self.send_restore_notification(backup_file, False, str(e))

    def restore_sqlite(self, backup_file, db_settings):
        """Restore SQLite database"""
        try:
            db_path = db_settings['NAME']
            
            # Close all database connections
            connection.close()
            
            # Backup current database
            if os.path.exists(db_path):
                backup_current = f"{db_path}.backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(db_path, backup_current)
                self.stdout.write(f"📁 Current database backed up to: {backup_current}")

            # Restore from backup
            shutil.copy2(backup_file, db_path)
            self.stdout.write("✅ SQLite database restored")
            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ SQLite restore failed: {e}"))
            return False

    def restore_postgresql(self, backup_file, db_settings):
        """Restore PostgreSQL database"""
        try:
            db_name = db_settings['NAME']
            db_user = db_settings.get('USER', '')
            db_password = db_settings.get('PASSWORD', '')
            db_host = db_settings.get('HOST', 'localhost')
            db_port = db_settings.get('PORT', '5432')

            # Set environment variable for password
            env = os.environ.copy()
            if db_password:
                env['PGPASSWORD'] = db_password

            # Drop and recreate database
            self.stdout.write("🗑️  Dropping existing database...")
            
            # Connect to postgres database to drop target database
            drop_cmd = [
                'psql', '-h', db_host, '-p', str(db_port), '-U', db_user,
                '-d', 'postgres', '-c', f'DROP DATABASE IF EXISTS "{db_name}";'
            ]
            subprocess.run(drop_cmd, env=env, check=True)

            # Create new database
            create_cmd = [
                'psql', '-h', db_host, '-p', str(db_port), '-U', db_user,
                '-d', 'postgres', '-c', f'CREATE DATABASE "{db_name}";'
            ]
            subprocess.run(create_cmd, env=env, check=True)

            # Restore from backup
            self.stdout.write("📥 Importing backup data...")
            restore_cmd = [
                'psql', '-h', db_host, '-p', str(db_port), '-U', db_user,
                '-d', db_name, '-f', backup_file
            ]
            
            result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.stdout.write("✅ PostgreSQL database restored")
                return True
            else:
                self.stdout.write(self.style.ERROR(f"❌ PostgreSQL restore failed: {result.stderr}"))
                return False

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("❌ psql command not found. Please install PostgreSQL client tools."))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ PostgreSQL restore failed: {e}"))
            return False

    def restore_mysql(self, backup_file, db_settings):
        """Restore MySQL database"""
        try:
            db_name = db_settings['NAME']
            db_user = db_settings.get('USER', '')
            db_password = db_settings.get('PASSWORD', '')
            db_host = db_settings.get('HOST', 'localhost')
            db_port = db_settings.get('PORT', '3306')

            # Drop and recreate database
            self.stdout.write("🗑️  Recreating database...")
            
            mysql_cmd = ['mysql', '-h', db_host, '-P', str(db_port), '-u', db_user]
            if db_password:
                mysql_cmd.append(f'-p{db_password}')
            
            # Drop and create database
            drop_create_sql = f"DROP DATABASE IF EXISTS `{db_name}`; CREATE DATABASE `{db_name}`;"
            subprocess.run(mysql_cmd + ['-e', drop_create_sql], check=True)

            # Restore from backup
            self.stdout.write("📥 Importing backup data...")
            with open(backup_file, 'r') as f:
                restore_cmd = mysql_cmd + [db_name]
                result = subprocess.run(restore_cmd, stdin=f, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.stdout.write("✅ MySQL database restored")
                return True
            else:
                self.stdout.write(self.style.ERROR(f"❌ MySQL restore failed: {result.stderr}"))
                return False

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("❌ mysql command not found. Please install MySQL client tools."))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ MySQL restore failed: {e}"))
            return False

    def preserve_superuser_access(self):
        """Ensure there's always a superuser account after restore"""
        from django.contrib.auth.models import User
        
        try:
            # Check if any superuser exists
            superuser_exists = User.objects.filter(is_superuser=True).exists()
            
            if not superuser_exists:
                self.stdout.write("⚠️  No superuser found after restore. Creating emergency superuser...")
                
                # Create emergency superuser
                emergency_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@localhost',
                    password='admin123',  # User should change this immediately
                    first_name='Emergency',
                    last_name='Admin'
                )
                
                self.stdout.write(
                    self.style.WARNING(
                        "🚨 Emergency superuser created:\n"
                        "   Username: admin\n"
                        "   Password: admin123\n"
                        "   ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!"
                    )
                )
            else:
                self.stdout.write("✅ Superuser account(s) preserved")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to preserve superuser access: {e}")
            )

    def create_superuser_interactive(self):
        """Create superuser interactively (kept for backward compatibility)"""
        try:
            self.stdout.write("\n👤 Creating additional superuser account...")
            call_command('createsuperuser', interactive=True)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Could not create superuser: {e}"))

    def send_restore_notification(self, backup_file, success, error_msg=None):
        """Send restore notification email"""
        try:
            admin_user = AdminUser.objects.first()
            business = Business.objects.first()

            if not admin_user or not admin_user.alerts_email:
                return

            # Get business name safely
            business_name = getattr(business, 'name', None) or getattr(business, 'business_name', None) or 'POS System'

            if success:
                subject = f'✅ Database Restore Successful'
                message = f"""
Database restore completed successfully.

Restore Details:
- Backup File: {backup_file}
- Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Business: {business_name}

Your system has been restored from backup.
Please verify all data is correct and test system functionality.
"""
            else:
                subject = f'❌ Database Restore Failed'
                message = f"""
Database restore failed.

Restore Details:
- Backup File: {backup_file}
- Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Business: {business_name}

Error: {error_msg}

Please check the system logs and try again.
Your original database should still be intact.
"""

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[admin_user.alerts_email]
            )
            email.send()

        except Exception as e:
            logger.error(f'Failed to send restore notification: {e}')