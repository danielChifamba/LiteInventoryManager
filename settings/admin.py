from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Business)
admin.site.register(General)
admin.site.register(AdminUser)
admin.site.register(ReceiptSettings)
admin.site.register(BackupLog)
admin.site.register(SecuritySettings)