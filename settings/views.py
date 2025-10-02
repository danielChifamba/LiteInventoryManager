from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.management import call_command
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.http import FileResponse

import re

from .forms import *

from .models import *

import os
import logging
from django.conf import settings

from .utils.reset import reset_system
from .utils.backup import backup_data, restore_data

logger = logging.getLogger(__name__)
def is_admin_user(user):
    """Check if user is admin"""
    try:
        return hasattr(user, 'is_admin')
    except:
        return user.is_superuser

@login_required
@user_passes_test(is_admin_user)
def settings_view(request):
    business = Business.objects.first()

    user = AdminUser.objects.get(user=request.user)

    general = General.objects.first()

    receipt = ReceiptSettings.objects.first()

    businessForm = BusinessSettingsForm(instance=business)
    generalForm = GeneralSettingsForm(instance=general)
    profileForm = ProfileSettingsForm(instance=user)
    receiptForm = ReceiptSettingsForm(instance=receipt)

    context = {
        'businessForm': businessForm,
        'generalForm': generalForm,
        'profileForm': profileForm,
        'receiptForm': receiptForm,

        'business': business,
        'profile': user,
        'general': general,
    }
    return render(request, 'settings/settings.html', context)

@login_required
@user_passes_test(is_admin_user)
def business_settings_view(request):
    business = Business.objects.first()
    if request.method == 'POST':
        form = BusinessSettingsForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, 'Business Settings successfully updated.')
            return redirect('settings:settings')
        else:
            messages.error(request, 'An error occured while updating business settings.')
    return redirect('settings:settings')


@login_required
@user_passes_test(is_admin_user)
def general_settings_view(request):
    general = General.objects.first()
    if request.method == 'POST':
        form = GeneralSettingsForm(request.POST, instance=general)
        if form.is_valid():
            form.save()
            messages.success(request, 'General Settings successfully updated.')
            return redirect('settings:settings')
        else:
            messages.error(request, 'An error occurred while updating general settings.')
    return redirect('settings:settings')



@login_required
@user_passes_test(is_admin_user)
def profile_settings_view(request):
    user = AdminUser.objects.get(user=request.user)
    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile Settings successfully updated.')
            return redirect('settings:settings')
        else:
            messages.error(request, 'An error occurred while updating profile settings.')
    return redirect('settings:settings')


@login_required
@user_passes_test(is_admin_user)
def receipt_settings_view(request):
    receipt = ReceiptSettings.objects.first()
    if request.method == 'POST':
        form = ReceiptSettingsForm(request.POST, instance=receipt)
        if form.is_valid():
            form.save()
            messages.success(request, 'Receipt Settings successfully updated.')
            return redirect('settings:settings')
        else:
            messages.error(request, 'An error occurred while updating receipt settings.')
    return redirect('settings:settings')

@login_required
@user_passes_test(is_admin_user)
def send_test_alerts(request):
    """Send test alert email (for testing purposes)"""
    try:
        # Check for admin permissions
        admin_user = AdminUser.objects.get(user=request.user)
        
        # Call management command to check stock and send alerts
        call_command('send_alerts', check_stock=True)
        
        messages.success(request, 'Alert check completed and notifications sent.')
        
    except AdminUser.DoesNotExist:
        messages.error(request, 'Only admin users can send test alerts.')
    except Exception as e:
        logger.error(f'Test alerts failed: {e}')
        messages.error(request, f'Failed to send test alerts: {str(e)}')
    
    return redirect('settings:settings')

@login_required
@user_passes_test(is_admin_user)
def backup_database_manual(request):
    """Manually trigger database backup"""
    try:
        # Check for admin permissions
        admin_user = AdminUser.objects.get(user=request.user)
        
        backup_type = 'manual'
        
        # Call management command
        call_command('backup_database', type=backup_type, email=True)
        
        messages.success(request, f'{backup_type.title()} backup completed successfully.')
        
    except AdminUser.DoesNotExist:
        messages.error(request, 'Only admin users can trigger backups.')
    except Exception as e:
        logger.error(f'Manual backup failed: {e}')
        messages.error(request, f'Failed to create backup: {str(e)}')
    
    return redirect('settings:settings')

@login_required
@user_passes_test(is_admin_user)
def restore_backup(request):
    """Restore from backup file"""
    if request.method == 'POST' and request.method == 'FILES':
        backup_file = request.POST['backup_file']
    
        if not backup_file or not os.path.exists(backup_file):
            messages.error(request, 'Invalid backup file selected.')
            return redirect('settings:settings')
        
        try:
            from django.core.management import call_command
            
            # Call the restore command
            call_command('restore_backup', backup_file, '--email', '--confirm')
            
            messages.success(request, 'Database restored successfully! Please check system functionality.')
            
        except Exception as e:
            messages.error(request, f'Restore failed: {str(e)}')
    
    return redirect('settings:settings')

@login_required
def manual_backup(request):
    try:
        file_path = backup_data()
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    except Exception as e:
        messages.error(request, f'Bakup failed: {e}')
        return redirect('settings:settings')

@login_required
def import_backup(request):
    if request.method == 'POST' and request.FILES.get('backup_file'):
        file = request.FILES['backup_file']
        path = os.path.join(settings.BASE_DIR, 'backups', file.name)
        with open(path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)
        try:
            restore_data(path)
            messages.success(request, 'Backup Restored Successfully.')
        except Exception as e:
            messages.error(request, f'Restore failed: {e}')
    
    return redirect('settings:settings')

@login_required
@user_passes_test(is_admin_user)
def reset_system_view(request):
    # delete all data in models
    reset_system()
    messages.success(request, 'System was reset successfully. username: admin | password: admin')
    return redirect('b_auth:login')
