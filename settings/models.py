from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from shortuuid.django_fields import ShortUUIDField
from datetime import datetime, timedelta
from b_auth.models import User


class AdminUser(models.Model):
    profile_picture = models.ImageField(upload_to="profile", blank=True, default="profile/profile_1.jpg")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # notification settings
    daily_report_email = models.EmailField(blank=True, null=True)
    alerts_email = models.BooleanField(default=True)
    low_stock_alerts = models.BooleanField(default=True)
    expense_alerts = models.BooleanField(default=True)
    enable_daily_reports = models.BooleanField(default=True)
    enable_alert_emails = models.BooleanField(default=True)
    enable_backup_notifications = models.BooleanField(default=True)
    backup_retention_days = models.PositiveIntegerField(default=30)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Admin: {self.user.get_full_name()}"
    

class Business(models.Model):

    business_logo = models.ImageField(upload_to="business-logo", blank=True, default="business-logo/logo.png")
    business_name = models.CharField(max_length=100, default='Business Name')
    business_address = models.CharField(max_length=255, default='123 Main Street, Gweru', blank=True)
    business_email = models.EmailField(unique=True, null=True, default='example@mailanator.com', blank=True)
    business_number = models.CharField(max_length=20, default='+263123456789', blank=True)
    business_website = models.URLField(max_length=100, default='businesssite.co.zw', blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    currency_symbol = models.CharField(max_length=3, default='$')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Business Details'

    def __str__(self):
        return self.business_name
    

class General(models.Model):
    DATE_CHOICES = [
        ('%Y-%m-%d','YYYY-DD-MM'),
        ('%m/%d/%Y','MM/DD/YYYY'),
        ('%d/%m/%Y','DD/MM/YYYY'),
        ('%b %d, %Y','Month DD, YYYY'),
        ('%B %d, %Y','Full month DD, YYYY'),
    ]
    BACKUP_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    THEME_CHOICES = [
        ('blue', 'Blue'),
        ('red', 'Red'),
        ('green', 'Green'),
        ('purple', 'Purple'),
        ('gold', 'Gold'),
    ]
    TIMEZONE_CHOICES = [
        ('Africa/Harare', 'Africa/Harare'),
        ('Africa/Cairo', 'Africa/Cairo'),
        ('Europe/London', 'Europe/London'),
        ('Europe/Paris', 'Europe/Paris'),
    ]
    date_format = models.CharField(max_length=100, default='%Y-%m-%d', choices=DATE_CHOICES)
    timezone = models.CharField(max_length=50, default='Africa/Harare', choices=TIMEZONE_CHOICES)
    backup_frequency = models.CharField(max_length=20, default='daily', choices=BACKUP_CHOICES)
    theme_color = models.CharField(max_length=20, default='blue', choices=THEME_CHOICES)
    auto_backup = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'General Settings'

    def __str__(self):
        return 'General Settings'

class ReceiptSettings(models.Model):
    show_logo = models.BooleanField(default=True)
    show_thank_you_note = models.BooleanField(default=True)
    thank_you_note = models.CharField(max_length=255, blank=True, default='Thank you for your purchase!')
    show_cashier_name = models.BooleanField(default=True)
    show_sales_time = models.BooleanField(default=True)

    # paper_size = models.CharField(max_length=20, default='A4')

    def __str__(self):
        return 'Receipt Settings'
    

class BackupLog(models.Model):
    file_name = models.CharField(max_length=255, default='backup')
    backup_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='success',choices=[('success','Success'), ('failed', 'Failed')])
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'{self.file_name} - {self.status}'


class SecuritySettings(models.Model):
    session_timeout_minutes = models.PositiveIntegerField(default=30)
    allow_multiple_logins = models.BooleanField(default=True)

    def __str__(self):
        return 'Security Settings'
