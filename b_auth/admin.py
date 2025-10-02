from django.contrib import admin
from .models import User, UserSession
from django.contrib.auth.admin import UserAdmin

# Register your models here.
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_admin', 'is_cashier', 'is_super')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {'fields': ('phone_number', )}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {'fields': ('phone_number', )}),
    )
    
    
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserSession)

admin.site.site_header = "NYDA Tech"
admin.site.site_title = "User Management"
admin.site.index_title = "Welcome Daniel Chief to dashboard"
