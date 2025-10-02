from django.core.management.base import BaseCommand
import logging
from django.conf import settings
from settings.models import *
from b_auth.models import User
from dashboard.models import *

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Setup system for use'

    def add_arguments(self, parser):
        parser.add_argument(
            '--init',
            action='store_true',
            help='Initialize the system for use'
        )

    def handle(self, *args, **options):
        try:
            if options['init']:
                self.initialize_system()

        except Exception as e:
            logger.error(f'Initialization processing failed: {e}')
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize the system: {e}')
            )

    def initialize_system(self):
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

        self.stdout.write(
            self.style.SUCCESS('✅ System initialized successfully.')
        )

            