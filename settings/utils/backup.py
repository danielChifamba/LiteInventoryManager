import os
import datetime
from django.core.management import call_command
from django.conf import settings
from settings.models import BackupLog

BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_data():
    today = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f'backup_{today}.json'
    file_path = os.path.join(BACKUP_DIR, file_name)

    try:
        with open(file_path, 'w') as f:
            call_command('dumpdata', exclude=['auth.permission', 'contenttypes'], stdout=f)
            BackupLog.objects.create(file_name=file_name, status='success', notes='Backup Completed Successfully')
            return file_path
    except Exception as e:
        BackupLog.objects.create(file_name=file_name, status='failed', notes=str(e))
        raise e

def restore_data(file_path):
    try:
        call_command('loaddata', file_path)
        return True
    except Exception as e:
        raise e