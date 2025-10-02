from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import F
from datetime import date
import logging

from dashboard.models import Alert, Product
from settings.models import Business, AdminUser, General

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send alert notifications via email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-stock',
            action='store_true',
            help='Check for low stock and create alerts'
        )

    def handle(self, *args, **options):
        try:
            if options['check_stock']:
                self.check_low_stock()

            # Send pending alerts
            self.send_alert_emails()

        except Exception as e:
            logger.error(f'Alert processing failed: {e}')
            self.stdout.write(
                self.style.ERROR(f'Failed to process alerts: {e}')
            )

    def check_low_stock(self):
        """Check for low stock products and create alerts"""
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            is_active=True
        )

        for product in low_stock_products:
            # Check if alert already exists for today
            existing_alert = Alert.objects.filter(
                alert_type='low_stock',
                title__icontains=product.name,
                created_at__date=date.today()
            ).exists()

            if not existing_alert:
                if product.is_out_of_stock():
                    Alert.objects.create(
                        alert_type='out_of_stock',
                        title=f'Out of Stock: {product.name}',
                        message=f'Product {product.name} (SKU: {product.sku}) is completely out of stock!'
                    )
                else:
                    Alert.objects.create(
                        alert_type='low_stock',
                        title=f'Low Stock: {product.name}',
                        message=f'Product {product.name} (SKU: {product.sku}) has only {product.stock_quantity} units left (minimum: {product.min_stock_level})'
                    )

        self.stdout.write(f'Checked {low_stock_products.count()} low stock products')

    def send_alert_emails(self):
        """Send unread alerts via email"""
        try:
            admin_user = AdminUser.objects.first()
            business = Business.objects.first()
            general = General.objects.first()

            if not admin_user or not admin_user.alerts_email or not admin_user.user.email:
                self.stdout.write(
                    self.style.WARNING('No alerts email configured')
                )
                return

            # Get unread alerts from today
            unread_alerts = Alert.objects.filter(
                is_read=False,
                created_at__date=date.today()
            ).order_by('-created_at')

            if not unread_alerts.exists():
                self.stdout.write('No new alerts to send')
                return

            # Group alerts by type
            alert_groups = {}
            for alert in unread_alerts:
                if alert.alert_type not in alert_groups:
                    alert_groups[alert.alert_type] = []
                alert_groups[alert.alert_type].append(alert)

            context = {
                'business': business,
                'alert_groups': alert_groups,
                'total_alerts': unread_alerts.count(),
                'date': date.today().strftime(general.date_format),
            }

            # Render email template
            html_content = render_to_string(
                'emails/alerts.html',
                context
            )
            text_content = render_to_string(
                'emails/alerts.txt',
                context
            )

            # Create email
            subject = f'System Alerts - {date.today().strftime(general.date_format)} | {business.business_name if business else "Business Name"}'
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[admin_user.user.email]
            )
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send()

            # Mark alerts as read after successful email send
            unread_alerts.update(is_read=True)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Sent {unread_alerts.count()} alerts to {admin_user.user.email}'
                )
            )

        except Exception as e:
            logger.error(f'Failed to send alert emails: {e}')
            self.stdout.write(
                self.style.ERROR(f'Failed to send alert emails: {e}')
            )