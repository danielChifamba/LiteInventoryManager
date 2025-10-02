import os
import subprocess
import datetime
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import EmailMessage
from settings.models import AdminUser, Business

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create database backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['daily', 'weekly', 'monthly', 'hourly'],
            default='daily',
            help='Backup type (daily, weekly, monthly)'
        )
        parser.add_argument(
            '--email',
            action='store_true',
            help='Send backup confirmation email'
        )

    def handle(self, *args, **options):
        backup_type = options['type']
        send_email = options['email']

        try:
            # Create backup directory if it doesn't exist
            backup_dir = getattr(settings, 'BACKUP_DIR', os.path.join(settings.BASE_DIR, 'backups'))
            os.makedirs(backup_dir, exist_ok=True)

            # Generate backup filename
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{backup_type}_backup_{timestamp}.sql'
            filepath = os.path.join(backup_dir, filename)

            # Get database settings
            db_settings = settings.DATABASES['default']
            db_name = db_settings['NAME']
            db_user = db_settings.get('USER', '')
            db_password = db_settings.get('PASSWORD', '')
            db_host = db_settings.get('HOST', 'localhost')
            db_port = db_settings.get('PORT', '5432')

            # Create backup command based on database engine
            if 'postgresql' in db_settings['ENGINE']:
                cmd = self.create_postgresql_backup_command(
                    db_name, db_user, db_password, db_host, db_port, filepath
                )
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            elif 'mysql' in db_settings['ENGINE']:
                cmd = self.create_mysql_backup_command(
                    db_name, db_user, db_password, db_host, db_port, filepath
                )
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            elif 'sqlite' in db_settings['ENGINE']:
                # For SQLite, use Python method instead of command line
                try:
                    if os.name == 'nt':  # Windows
                        import shutil
                        shutil.copy2(db_name, filepath)
                        result = type('Result', (), {'returncode': 0, 'stderr': ''})()
                    else:
                        cmd = self.create_sqlite_backup_command(db_name, filepath)
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                except Exception as e:
                    result = type('Result', (), {'returncode': 1, 'stderr': str(e)})()
            else:
                raise Exception(f"Unsupported database engine: {db_settings['ENGINE']}")

            # Execute backup command
            self.stdout.write(f'Creating {backup_type} backup...')
            # result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # Moved above

            if result.returncode == 0:
                file_size = os.path.getsize(filepath)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Backup created successfully: {filename} ({file_size} bytes)'
                    )
                )

                # Clean old backups
                self.cleanup_old_backups(backup_dir, backup_type)

                # Send email notification if requested
                if send_email:
                    self.send_backup_notification(filename, file_size, backup_type, True)

            else:
                error_msg = f'Backup failed: {result.stderr}'
                logger.error(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))
                
                if send_email:
                    self.send_backup_notification(filename, 0, backup_type, False, result.stderr)

        except Exception as e:
            logger.error(f'Backup process failed: {e}')
            self.stdout.write(self.style.ERROR(f'Backup failed: {e}'))
            
            if send_email:
                self.send_backup_notification('', 0, backup_type, False, str(e))

    def create_postgresql_backup_command(self, db_name, db_user, db_password, db_host, db_port, filepath):
        """Create PostgreSQL backup command"""
        env_vars = ""
        if db_password:
            env_vars = f"PGPASSWORD='{db_password}' "
        
        return f"{env_vars}pg_dump -h {db_host} -p {db_port} -U {db_user} -d {db_name} > {filepath}"

    def create_mysql_backup_command(self, db_name, db_user, db_password, db_host, db_port, filepath):
        """Create MySQL backup command"""
        password_option = f"-p'{db_password}'" if db_password else ""
        return f"mysqldump -h {db_host} -P {db_port} -u {db_user} {password_option} {db_name} > {filepath}"

    def create_sqlite_backup_command(self, db_path, filepath):
        """Create SQLite backup command"""
        import shutil
        import os
        
        # For Windows, use Python's shutil.copy2 instead of sqlite3 command
        if os.name == 'nt':  # Windows
            try:
                shutil.copy2(db_path, filepath)
                return True
            except Exception as e:
                raise Exception(f"Failed to copy SQLite database: {e}")
        else:
            # For Unix/Linux systems, try to find sqlite3
            sqlite_cmd = self.find_sqlite_command()
            return f"{sqlite_cmd} {db_path} '.backup {filepath}'"
    
    def find_sqlite_command(self):
        """Find the sqlite3 command path"""
        import shutil
        
        # Try common sqlite3 command locations
        sqlite_paths = ['sqlite3', '/usr/bin/sqlite3', '/usr/local/bin/sqlite3']
        
        for cmd in sqlite_paths:
            if shutil.which(cmd):
                return cmd
        
        # If not found, raise an error with helpful message
        raise Exception(
            "sqlite3 command not found. Please install SQLite3 or use Python backup method."
        )

    def cleanup_old_backups(self, backup_dir, backup_type):
        """Clean up old backup files"""
        retention_days = {
            'daily': 30,    # Keep daily backups for 30 days
            'weekly': 90,   # Keep weekly backups for 90 days
            'monthly': 365  # Keep monthly backups for 1 year
        }

        cutoff_date = datetime.datetime.now() - datetime.timedelta(
            days=retention_days.get(backup_type, 30)
        )

        try:
            for filename in os.listdir(backup_dir):
                if filename.startswith(f'{backup_type}_backup_'):
                    filepath = os.path.join(backup_dir, filename)
                    file_time = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        self.stdout.write(f'Removed old backup: {filename}')

        except Exception as e:
            logger.warning(f'Failed to cleanup old backups: {e}')

    def send_backup_notification(self, filename, file_size, backup_type, success, error_msg=None):
        """Send backup notification email"""
        try:
            admin_user = AdminUser.objects.first()
            business = Business.objects.first()

            if not admin_user or not admin_user.alerts_email:
                return

            # Get business name safely
            business_name = getattr(business, 'name', None) or getattr(business, 'business_name', None) or 'POS System'

            if success:
                subject = f'✅ {backup_type.title()} Backup Successful'
                message = f"""
Database backup completed successfully.

Backup Details:
- Type: {backup_type.title()}
- Filename: {filename}
- Size: {file_size:,} bytes
- Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Business: {business_name}

Your data is safely backed up.
"""
            else:
                subject = f'❌ {backup_type.title()} Backup Failed'
                message = f"""
Database backup failed.

Backup Details:
- Type: {backup_type.title()}
- Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Business: {business_name}

Error: {error_msg}

Please check the system logs and try again.
"""

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[admin_user.alerts_email]
            )
            email.send()

        except Exception as e:
            logger.error(f'Failed to send backup notification: {e}')