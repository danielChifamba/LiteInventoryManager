from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('The username field must be set')
        if not email:
            raise ValueError('The email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'super')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff set to True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have value is_superuset set to True')

        return self.create_user(username, email, password, **extra_fields)
    
    def create_cashier(self, username, email, password, first_name, last_name, phone_number=None):
        extra_fields = {
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': phone_number,
            'user_type': 'cashier',
            'is_staff': False,
            'is_superuser': False
        }
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('cashier', 'Cashier'),
        ('super', 'Super'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='admin')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def is_admin(self):
        return self.user_type == 'admin'
    
    @property
    def is_cashier(self):
        return self.user_type == 'cashier'

    @property
    def is_super(self):
        return self.user_type == 'super'

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.login_time} - {self.is_active}"
