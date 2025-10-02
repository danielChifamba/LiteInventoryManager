from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from datetime import date, timedelta
import logging

from dashboard.models import (
    Sale, SaleItem, Product, Expense, DailyReport, 
    Alert, Cashier, Category
)
from settings.models import Business, AdminUser, General

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate and send daily report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date for report (YYYY-MM-DD format), defaults to yesterday'
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Send email notification'
        )

    def handle(self, *args, **options):
        try:
            # Get report date
            if options['date']:
                report_date = timezone.datetime.strptime(options['date'], '%Y-%m-%d').date()
            else:
                report_date = date.today() - timedelta(days=1)

            self.stdout.write(f'Generating daily report for {report_date}')

            # Generate report
            report_data = self.generate_daily_report(report_date)
            
            # Create or update daily report record
            daily_report, created = DailyReport.objects.update_or_create(
                date=report_date,
                defaults=report_data
            )

            # Send email if requested
            if options['send_email']:
                self.send_daily_report_email(daily_report, report_data)

            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(
                    f'{action} daily report for {report_date}'
                )
            )

        except Exception as e:
            logger.error(f'Daily report generation failed: {e}')
            self.stdout.write(
                self.style.ERROR(f'Failed to generate daily report: {e}')
            )

    def generate_daily_report(self, report_date):
        """Generate comprehensive daily report data"""
        
        # Sales data
        daily_sales = Sale.objects.filter(created_at__date=report_date)
        total_sales = daily_sales.aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )

        # Payment method breakdown
        payment_breakdown = daily_sales.aggregate(
            cash=Sum('total_amount', filter=Q(payment_method='cash')),
            card=Sum('total_amount', filter=Q(payment_method='card')),
            mobile=Sum('total_amount', filter=Q(payment_method='mobile'))
        )

        # Expenses
        daily_expenses = Expense.objects.filter(
            date=report_date, 
            is_active=True
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )

        # Top selling product
        top_product_data = SaleItem.objects.filter(
            sale__created_at__date=report_date
        ).values('product').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_quantity').first()

        top_selling_product = None
        if top_product_data:
            top_selling_product = Product.objects.get(
                id=top_product_data['product']
            )

        # Profit calculation
        daily_sale_items = SaleItem.objects.filter(
            sale__created_at__date=report_date
        )
        gross_profit = sum(item.get_profit() for item in daily_sale_items)
        net_profit = gross_profit - (daily_expenses['total'] or 0)

        return {
            'total_sales': total_sales['total'] or 0,
            'total_transactions': total_sales['count'] or 0,
            'total_expenses': daily_expenses['total'] or 0,
            'cash_sales': payment_breakdown['cash'] or 0,
            'card_sales': payment_breakdown['card'] or 0,
            'mobile_sales': payment_breakdown['mobile'] or 0,
            'top_selling_product': top_selling_product,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
        }

    def send_daily_report_email(self, daily_report, report_data):
        """Send daily report via email"""
        try:
            # Get business settings
            business = Business.objects.first()
            admin_user = AdminUser.objects.first()
            general = General.objects.first()

            if not admin_user or not admin_user.daily_report_email:
                self.stdout.write(
                    self.style.WARNING('No daily report email configured')
                )
                return

            # Get additional data for email
            low_stock_count = Product.objects.filter(
                stock_quantity__lte=F('min_stock_level'),
                is_active=True
            ).count()

            recent_alerts = Alert.objects.filter(
                created_at__date=daily_report.date,
                is_read=False
            ).count()

            # Calculate week comparison
            last_week_date = daily_report.date - timedelta(days=7)
            last_week_report = DailyReport.objects.filter(
                date=last_week_date
            ).first()

            week_comparison = None
            if last_week_report:
                sales_change = (
                    (daily_report.total_sales - last_week_report.total_sales) / 
                    last_week_report.total_sales * 100 
                    if last_week_report.total_sales > 0 else 0
                )
                week_comparison = {
                    'sales_change': sales_change,
                    'last_week_sales': last_week_report.total_sales
                }

            context = {
                'business': business,
                'daily_report': daily_report,
                'report_data': report_data,
                'low_stock_count': low_stock_count,
                'recent_alerts': recent_alerts,
                'week_comparison': week_comparison,
                'report_date': daily_report.date.strftime(general.date_format),
            }

            # Render email template
            html_content = render_to_string(
                'emails/daily_report.html', 
                context
            )
            text_content = render_to_string(
                'emails/daily_report.txt',
                context
            )

            # Create email
            subject = f'Daily Report - {daily_report.date.strftime(general.date_format)} | {business.business_name if business else "Business Name"}'
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[admin_user.daily_report_email]
            )
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Daily report email sent to {admin_user.daily_report_email}'
                )
            )

        except Exception as e:
            logger.error(f'Failed to send daily report email: {e}')
            self.stdout.write(
                self.style.ERROR(f'Failed to send email: {e}')
            )