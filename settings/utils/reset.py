from django.contrib.auth import get_user_model
from dashboard.models import *
from settings.models import *
from settings.init import initialize_system

User = get_user_model()

def reset_system():
    print('⚠️ Warning: Resetting system data...')

    Cashier.objects.all().delete()
    SaleItem.objects.all().delete()
    Sale.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    StockMovement.objects.all().delete()
    Expense.objects.all().delete()
    ExpenseCategory.objects.all().delete()
    Alert.objects.all().delete()
    DailyReport.objects.all().delete()

    # settings and logs
    Business.objects.all().delete()
    General.objects.all().delete()
    ReceiptSettings.objects.all().delete()
    SecuritySettings.objects.all().delete()
    BackupLog.objects.all().delete()

    for user in User.objects.exclude(is_superuser=True):
        user.delete()

    AdminUser.objects.all().delete()    

    # call init to initialize the system again
    initialize_system()

    print('✅ System reset complete.')
