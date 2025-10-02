# management/commands/manage_backup_scheduler.py
"""
Django management command to control the backup scheduler
Place this in: settings/management/commands/manage_backup_scheduler.py
"""

import os
import sys
import time
import logging
import schedule
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

# Import the backup scheduler
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backup_scheduler import BackupScheduler

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Manage the automated backup scheduler'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status', 'test', 'install-service', 'remove-service'],
            help='Action to perform'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run scheduler as a daemon (background process)'
        )
        parser.add_argument(
            '--test-frequency',
            choices=['daily', 'weekly', 'monthly', 'hourly'],
            help='Test backup with specific frequency'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'start':
            self.start_scheduler(options.get('daemon', False))
            
        elif action == 'stop':
            self.stop_scheduler()
            
        elif action == 'status':
            self.show_status()
            
        elif action == 'test':
            self.test_backup(options.get('test_frequency', 'daily'))
            
        elif action == 'install-service':
            self.install_windows_service()
            
        elif action == 'remove-service':
            self.remove_windows_service()
            
        else:
            raise CommandError(f'Unknown action: {action}')

    def start_scheduler(self, daemon=False):
        """Start the backup scheduler"""
        try:
            scheduler = BackupScheduler()
            
            if daemon:
                self.stdout.write("Starting backup scheduler as daemon...")
                scheduler.start()
                
                # Create PID file
                pid_file = os.path.join(settings.BASE_DIR, 'backup_scheduler.pid')
                with open(pid_file, 'w') as f:
                    f.write(str(os.getpid()))
                
                self.stdout.write(
                    self.style.SUCCESS("Backup scheduler started in background")
                )
                
                # Keep main process alive
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.stdout.write("Shutting down scheduler...")
                    scheduler.stop()
                    if os.path.exists(pid_file):
                        os.remove(pid_file)
                    
            else:
                self.stdout.write("Starting backup scheduler...")
                frequency = scheduler.get_backup_frequency()
                backup_time = scheduler.get_backup_time()
                
                self.stdout.write(f"Backup frequency: {frequency}")
                self.stdout.write(f"Backup time: {backup_time}")
                
                scheduler.schedule_backups()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        "Scheduler configured. Use --daemon to run in background."
                    )
                )
                
        except Exception as e:
            raise CommandError(f'Failed to start scheduler: {e}')

    def stop_scheduler(self):
        """Stop the backup scheduler"""
        try:
            pid_file = os.path.join(settings.BASE_DIR, 'backup_scheduler.pid')
            
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                    
                try:
                    import signal
                    os.kill(pid, signal.SIGTERM)
                    os.remove(pid_file)
                    self.stdout.write(
                        self.style.SUCCESS("Backup scheduler stopped")
                    )
                except ProcessLookupError:
                    os.remove(pid_file)
                    self.stdout.write("Scheduler was not running")
                    
            else:
                self.stdout.write("No scheduler PID file found")
                
        except Exception as e:
            raise CommandError(f'Failed to stop scheduler: {e}')

    def show_status(self):
        """Show scheduler status and settings"""
        try:
            scheduler = BackupScheduler()
            frequency = scheduler.get_backup_frequency()
            backup_time = scheduler.get_backup_time()
            
            self.stdout.write("=== Backup Scheduler Status ===")
            self.stdout.write(f"Backup frequency: {frequency}")
            self.stdout.write(f"Backup time: {backup_time}")
            
            # Check if scheduler is running
            pid_file = os.path.join(settings.BASE_DIR, 'backup_scheduler.pid')
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                self.stdout.write(f"Scheduler running with PID: {pid}")
            else:
                self.stdout.write("Scheduler is not running")
            
            # Show recent backups
            backup_dir = getattr(settings, 'BACKUP_DIR', os.path.join(settings.BASE_DIR, 'backups'))
            if os.path.exists(backup_dir):
                backups = [f for f in os.listdir(backup_dir) if f.endswith('.sql')]
                backups.sort(key=lambda x: os.path.getctime(os.path.join(backup_dir, x)), reverse=True)
                
                self.stdout.write("\n=== Recent Backups ===")
                for backup in backups[:5]:  # Show last 5 backups
                    filepath = os.path.join(backup_dir, backup)
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                    self.stdout.write(f"{backup} ({size:,} bytes) - {mtime_str}")
                    
        except Exception as e:
            raise CommandError(f'Failed to get status: {e}')

    def test_backup(self, frequency='daily'):
        """Test backup functionality"""
        try:
            self.stdout.write(f"Testing {frequency} backup...")
            
            scheduler = BackupScheduler()
            scheduler.run_backup(frequency)
            
            self.stdout.write(
                self.style.SUCCESS(f"{frequency} backup test completed")
            )
            
        except Exception as e:
            raise CommandError(f'Backup test failed: {e}')

    def install_windows_service(self):
        """Install the Windows service (Windows only)"""
        try:
            import platform
            if platform.system() != 'Windows':
                raise CommandError('Windows service installation only available on Windows')
                
            from windows_backup_service import install_service
            install_service()
            
            self.stdout.write(
                self.style.SUCCESS("Windows service installed successfully")
            )
            
        except ImportError:
            raise CommandError(
                'Windows service modules not available. '
                'Install pywin32: pip install pywin32'
            )
        except Exception as e:
            raise CommandError(f'Failed to install Windows service: {e}')

    def remove_windows_service(self):
        """Remove the Windows service (Windows only)"""
        try:
            import platform
            if platform.system() != 'Windows':
                raise CommandError('Windows service removal only available on Windows')
                
            from windows_backup_service import remove_service
            remove_service()
            
            self.stdout.write(
                self.style.SUCCESS("Windows service removed successfully")
            )
            
        except ImportError:
            raise CommandError(
                'Windows service modules not available. '
                'Install pywin32: pip install pywin32'
            )
        except Exception as e:
            raise CommandError(f'Failed to remove Windows service: {e}')