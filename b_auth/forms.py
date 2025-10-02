from django import forms
from .models import User

from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

# Admin Login Form
class AdminLoginForm(forms.Form):
    USERNME_ATTR = {
        'placeholder':'Username',
        'class':'form-control',
        'id':'floatingInput',
    }

    PASSWORD_ATTR = {
        'placeholder':'Password',
        'class':'form-control',
        'id':'floatingInput',
    }

    username = forms.CharField(max_length=255, widget=forms.TextInput(attrs=USERNME_ATTR))
    password = forms.CharField(max_length=255, widget=forms.PasswordInput(attrs=PASSWORD_ATTR))

# Cashier Login Form
class CashierLoginForm(forms.Form):
    USERNAME_ATTR = {
        'id':'sellerId',
        'name':'sellerId',
        'required': True,
    }

    PASSWORD_ATTR = {
        'id':'password',
        'name':'password',
        'required': True,
    }

    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs=USERNAME_ATTR))
    password = forms.CharField(max_length=200, widget=forms.PasswordInput(attrs=PASSWORD_ATTR))

# Reset Password Form
class ResetPasswordForm(forms.Form):
    EMAIL_ATTR = {
        'class':'form-control',
        'id':'email',
        'required': True,
    }

    NEW_PASSWORD_ATTR = {
        'class':'form-control',
        'id':'password',
        'required': True,
    }

    CONFIRM_PASSWORD = {
        'class':'form-control',
        'id':'confirm_password',
        'required': True,
    }

    email = forms.EmailField(widget=forms.EmailInput(attrs=EMAIL_ATTR))
    new_password = forms.CharField(max_length=255, widget=forms.PasswordInput(attrs=NEW_PASSWORD_ATTR), help_text='Password must be at least 8 charcters long')
    confirm_password = forms.CharField(max_length=255, widget=forms.PasswordInput(attrs=CONFIRM_PASSWORD))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            self.user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError('No user found with this email address.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError('Passwords do not match.')

        return cleaned_data

    def save(self):
        if hasattr(self, 'user'):
            self.user.set_password(self.cleaned_data['new_password'])
            self.user.save()
            return self.user
        return None