from django.contrib.auth import get_user_model
from django.conf import settings
from .models import *
from b_auth.models import User
from dashboard.models import ExpenseCategory

def initialize_system():
    if not Business.objects.exists():
        Business.objects.create()

    if not General.objects.exists():
        general = General.objects.create()
        settings.TIME_ZONE = general.timezone

    if not ReceiptSettings.objects.exists():
        ReceiptSettings.objects.create()

    if not SecuritySettings.objects.exists():
        SecuritySettings.objects.create()

    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser(username='super', password='admin12345', email='super@example.com')
    
    if not AdminUser.objects.exists():
        user = User.objects.create_user(username='admin', password='admin', email='admin@example.com', first_name='Admin', last_name='User', phone_number='+263123456789')
        AdminUser.objects.create(user=user)

    if not ExpenseCategory.objects.exists():
        ExpenseCategory.objects.create(name='Office Supplies', description='Costs associated with purchasing materials and equipment necessary for daily office operations, such as paper, pens, printers, and stationery.')

        ExpenseCategory.objects.create(name='Marketing', description='Expenses related to promoting the business, including advertising, social media, content creation, and event sponsorships.')

        ExpenseCategory.objects.create(name='Utilities', description='Costs of essential services required to operate the business, such as electricity, water, gas, internet, and phone services.')

        ExpenseCategory.objects.create(name='Transportation', description='Expenses related to business travel, including fuel, parking, public transportation, and vehicle maintenance.')

        ExpenseCategory.objects.create(name='Others', description='Miscellaneous expenses that do not fit into other categories, such as subscriptions, memberships, or unexpected costs.')