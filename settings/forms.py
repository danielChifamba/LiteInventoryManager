from django import forms
from django.core.validators import RegexValidator
from .models import General, Business, General, AdminUser, ReceiptSettings

class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = [
            'business_logo',
            'business_name',
            'business_address',
            'business_email',
            'business_number',
            'business_website',
            'tax_rate',
            'currency_symbol',
        ]
        widgets = {
            'business_logo': forms.FileInput(attrs={'class':'form-control', 'id':'business_logo_pick', 'style': 'display: none'}),
            'business_name': forms.TextInput(attrs={'class':'form-control','id':'name'}),
            'business_address': forms.TextInput(attrs={'class':'form-control','id':'address'}),
            'business_email': forms.EmailInput(attrs={'class':'form-control','id':'email'}),
            'business_number': forms.TextInput(attrs={'class':'form-control','id':'number'}),
            'business_website': forms.TextInput(attrs={'class':'form-control','id':'website'}),
            'tax_rate': forms.NumberInput(attrs={'class':'form-control','id':'rate'}),
            'currency_symbol': forms.TextInput(attrs={'class':'form-control','id':'currency_symbol'}),
        }

class GeneralSettingsForm(forms.ModelForm):
    class Meta:
        model = General
        fields = [
            'date_format',
            'timezone',
            'backup_frequency',
            'theme_color',
            'auto_backup',
            'dark_mode'
        ]
        widgets = {
            'date_format': forms.Select(attrs={'class':'form-control','id':'date_format'}),
            'timezone': forms.Select(attrs={'class':'form-control','id':'timezone'}),
            'backup_frequency': forms.Select(attrs={'class':'form-control','id':'backup_frequency'}),
            'theme_color': forms.Select(attrs={'class':'form-control','id':'theme'}),
            'auto_backup': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'auto_backup'}),
            'dark_mode': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'dark_mode'}),
        }

class ProfileSettingsForm(forms.ModelForm):
    email =  forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control','id':'email'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','id':'phone_number'}))

    class Meta:
        model = AdminUser
        fields = [
            'profile_picture',
            'daily_report_email',
            'alerts_email',
            'low_stock_alerts',
            'expense_alerts',
            'enable_daily_reports',
            'enable_alert_emails',
            'enable_backup_notifications'
        ]
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class':'form-control','id':'profile_pic_pick','style': 'display: none'}),
            'daily_report_email': forms.EmailInput(attrs={'class':'form-control','id':'report'}),
            'alerts_email': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'email_alert'}),
            'low_stock_alerts': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'low_stock_alert'}),
            'expense_alerts': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'expense_alert'}),
            'enable_daily_reports': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'expense_alert'}),
            'enable_alert_emails': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'expense_alert'}),
            'enable_backup_notifications': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'expense_alert'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProfileSettingsForm, self).__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'user'):
            self.initial['email'] = self.instance.user.email
            self.initial['phone_number'] = self.instance.user.phone_number

    def save(self, commit=True):
        admin_user = super(ProfileSettingsForm, self).save(commit=False)
        admin_user.user.email = self.cleaned_data['email']
        admin_user.user.phone_number = self.cleaned_data['phone_number']
        if commit:
            admin_user.user.save()
            admin_user.save()
        return admin_user

class ReceiptSettingsForm(forms.ModelForm):
    class Meta:
        model = ReceiptSettings
        fields = [
            'thank_you_note',
            'show_logo',
            'show_thank_you_note',
            'show_cashier_name',
            'show_sales_time',
        ]
        widgets = {
            'thank_you_note': forms.Textarea(attrs={'class':'form-control','id':'thank_you_note','rows': 2,'cols': 20}),
            'show_logo': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'show_logo'}),
            'show_thank_you_note': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'show_thank_you_note'}),
            'show_cashier_name': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'show_cashier_name'}),
            'show_sales_time': forms.CheckboxInput(attrs={'class':'form-control form-check-input','id':'email'}),
        }
        
class BackupRestoreForm(forms.Form):
    backup_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.db,.sql'
        }),
        help_text='Select a backup file (.db for SQLite, .sql for PostgreSQL/MySQL)'
    )
    
    confirm_restore = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I understand this will replace all current data'
    )

