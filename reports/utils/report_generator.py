# management/commands/generate_daily_report.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Max, F, Q
from django.core.mail import EmailMessage
from django.conf import settings
from datetime import date, timedelta
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from dashboard.models import (
    Sale, SaleItem, Product, Expense, DailyReport, 
    Category, Cashier, StockMovement
)

class Command(BaseCommand):
    help = 'Generate daily report PDF and optionally send via email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date for report (YYYY-MM-DD). Defaults to yesterday',
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Send report via email',
        )
        parser.add_argument(
            '--email-to',
            type=str,
            help='Email address to send report to',
        )

    def handle(self, *args, **options):
        # Get report date (default to yesterday)
        if options['date']:
            report_date = timezone.datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            report_date = date.today() - timedelta(days=1)

        self.stdout.write(f'Generating daily report for {report_date}...')

        # Generate or update daily report
        daily_report, created = DailyReport.objects.get_or_create(
            date=report_date,
            defaults=self._get_default_report_data(report_date)
        )

        if not created:
            # Update existing report
            report_data = self._get_default_report_data(report_date)
            for key, value in report_data.items():
                setattr(daily_report, key, value)
            daily_report.save()

        # Generate detailed report data
        report_data = self._generate_detailed_report(report_date, daily_report)

        # Create PDF report
        pdf_path = self._create_pdf_report(report_date, report_data)

        # Send email if requested
        if options['send_email']:
            email_to = options['email_to'] or getattr(settings, 'ADMIN_EMAIL', None)
            if email_to:
                self._send_email_report(report_date, pdf_path, email_to)
            else:
                self.stdout.write(
                    self.style.WARNING('No email address provided. Use --email-to or set ADMIN_EMAIL in settings.')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Daily report for {report_date} generated successfully!')
        )

    def _get_default_report_data(self, report_date):
        """Generate basic report data for DailyReport model"""
        sales_data = Sale.objects.filter(created_at__date=report_date).aggregate(
            total_sales=Sum('total_amount'),
            total_transactions=Count('id'),
            cash_sales=Sum('total_amount', filter=Q(payment_method='cash')),
            card_sales=Sum('total_amount', filter=Q(payment_method='card')),
            mobile_sales=Sum('total_amount', filter=Q(payment_method='mobile')),
        )

        expenses_data = Expense.objects.filter(date=report_date).aggregate(
            total_expenses=Sum('amount')
        )

        # Get top selling product
        top_product = Product.objects.filter(
            saleitem__sale__created_at__date=report_date
        ).annotate(
            total_sold=Sum('saleitem__quantity')
        ).order_by('-total_sold').first()

        return {
            'total_sales': sales_data['total_sales'] or 0,
            'total_expenses': expenses_data['total_expenses'] or 0,
            'total_transactions': sales_data['total_transactions'] or 0,
            'cash_sales': sales_data['cash_sales'] or 0,
            'card_sales': sales_data['card_sales'] or 0,
            'mobile_sales': sales_data['mobile_sales'] or 0,
            'top_selling_product': top_product,
        }

    def _generate_detailed_report(self, report_date, daily_report):
        """Generate detailed report data for PDF"""
        
        # Sales summary
        sales = Sale.objects.filter(created_at__date=report_date)
        
        # Product performance
        top_products = Product.objects.filter(
            saleitem__sale__created_at__date=report_date
        ).annotate(
            total_sold=Sum('saleitem__quantity'),
            revenue=Sum('saleitem__total_price'),
        ).order_by('-total_sold')[:10]

        # Cashier performance
        cashier_performance = Cashier.objects.filter(
            sale__created_at__date=report_date
        ).annotate(
            total_sales=Sum('sale__total_amount'),
            total_transactions=Count('sale')
        ).order_by('-total_sales')

        # Stock movements
        stock_movements = StockMovement.objects.filter(
            created_at__date=report_date
        ).select_related('product')

        # Low stock alerts
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            is_active=True
        )

        # Expenses by category
        expense_categories = Expense.objects.filter(
            date=report_date
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')

        return {
            'date': report_date,
            'summary': {
                'total_sales': daily_report.total_sales,
                'total_expenses': daily_report.total_expenses,
                'net_profit': daily_report.total_sales - daily_report.total_expenses,
                'total_transactions': daily_report.total_transactions,
                'average_transaction': daily_report.total_sales / daily_report.total_transactions if daily_report.total_transactions > 0 else 0,
            },
            'payment_methods': {
                'cash': daily_report.cash_sales,
                'card': daily_report.card_sales,
                'mobile': daily_report.mobile_sales,
            },
            'top_products': top_products,
            'cashier_performance': cashier_performance,
            'stock_movements': stock_movements,
            'low_stock_alerts': low_stock_products,
            'expenses': expense_categories,
        }

    def _create_pdf_report(self, report_date, report_data):
        """Create PDF report using ReportLab"""
        reports_dir = os.path.join(settings.BASE_DIR, 'reports', 'daily')
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f'daily_report_{report_date.strftime("%Y_%m_%d")}.pdf'
        filepath = os.path.join(reports_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Title
        title = Paragraph(f"Daily Sales Report - {report_date.strftime('%B %d, %Y')}", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Sales', f"${report_data['summary']['total_sales']:,.2f}"],
            ['Total Expenses', f"${report_data['summary']['total_expenses']:,.2f}"],
            ['Net Profit', f"${report_data['summary']['net_profit']:,.2f}"],
            ['Total Transactions', f"{report_data['summary']['total_transactions']:,}"],
            ['Average Transaction', f"${report_data['summary']['average_transaction']:,.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Payment Methods Breakdown
        story.append(Paragraph("Payment Methods", heading_style))
        
        payment_data = [
            ['Payment Method', 'Amount', 'Percentage'],
            ['Cash', f"${report_data['payment_methods']['cash']:,.2f}", 
             f"{(report_data['payment_methods']['cash'] / report_data['summary']['total_sales'] * 100) if report_data['summary']['total_sales'] > 0 else 0:.1f}%"],
            ['Card', f"${report_data['payment_methods']['card']:,.2f}", 
             f"{(report_data['payment_methods']['card'] / report_data['summary']['total_sales'] * 100) if report_data['summary']['total_sales'] > 0 else 0:.1f}%"],
            ['Mobile Money', f"${report_data['payment_methods']['mobile']:,.2f}", 
             f"{(report_data['payment_methods']['mobile'] / report_data['summary']['total_sales'] * 100) if report_data['summary']['total_sales'] > 0 else 0:.1f}%"],
        ]
        
        payment_table = Table(payment_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(payment_table)
        story.append(Spacer(1, 20))
        
        # Top Selling Products
        if report_data['top_products']:
            story.append(Paragraph("Top Selling Products", heading_style))
            
            products_data = [['Product', 'SKU', 'Qty Sold', 'Revenue']]
            for product in report_data['top_products'][:10]:
                products_data.append([
                    product.name[:30] + '...' if len(product.name) > 30 else product.name,
                    product.sku,
                    str(product.total_sold),
                    f"${product.revenue:,.2f}"
                ])
            
            products_table = Table(products_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch])
            products_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(products_table)
            story.append(Spacer(1, 20))
        
        # Cashier Performance
        if report_data['cashier_performance']:
            story.append(Paragraph("Cashier Performance", heading_style))
            
            cashier_data = [['Cashier', 'Sales Amount', 'Transactions']]
            for cashier in report_data['cashier_performance']:
                cashier_data.append([
                    cashier.user.get_full_name(),
                    f"${cashier.total_sales:,.2f}",
                    str(cashier.total_transactions)
                ])
            
            cashier_table = Table(cashier_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            cashier_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(cashier_table)
            story.append(Spacer(1, 20))
        
        # Stock Alerts
        if report_data['low_stock_alerts']:
            story.append(Paragraph("Low Stock Alerts", heading_style))
            
            stock_data = [['Product', 'SKU', 'Current Stock', 'Min Level']]
            for product in report_data['low_stock_alerts']:
                stock_data.append([
                    product.name[:25] + '...' if len(product.name) > 25 else product.name,
                    product.sku,
                    str(product.stock_quantity),
                    str(product.min_stock_level)
                ])
            
            stock_table = Table(stock_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
            stock_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stock_table)
            story.append(Spacer(1, 20))
        
        # Expenses
        if report_data['expenses']:
            story.append(Paragraph("Expenses by Category", heading_style))
            
            expense_data = [['Category', 'Amount']]
            for expense in report_data['expenses']:
                expense_data.append([
                    expense['category__name'],
                    f"${expense['total']:,.2f}"
                ])
            
            expense_table = Table(expense_data, colWidths=[3*inch, 1.5*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(expense_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        footer = Paragraph(f"Report generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style)
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        
        self.stdout.write(f'PDF report saved: {filepath}')
        return filepath

    def _send_email_report(self, report_date, pdf_path, email_to):
        """Send PDF report via email"""
        subject = f'Daily Sales Report - {report_date.strftime("%B %d, %Y")}'
        
        body = f"""
Dear Admin,

Please find attached the daily sales report for {report_date.strftime('%B %d, %Y')}.

Best regards,
POS System
        """
        
        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_to],
            )
            email.attach_file(pdf_path)
            email.send()
            
            self.stdout.write(f'Report emailed to: {email_to}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send email: {str(e)}'),
              ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            )
            
            story.append(table)
        else:
            story.append(Paragraph("No sales data available for this date.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        return story

    def _generate_inventory_alerts(self):
        """Generate inventory alerts section"""
        story = []
        story.append(Paragraph("Inventory Alerts", self.styles['Heading2']))
        
        # Get low stock and out of stock products
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=models.F('min_stock_level'),
            is_active=True
        ).order_by('stock_quantity')[:20]
        
        if low_stock_products:
            data = [['Product', 'SKU', 'Current Stock', 'Min Level', 'Status']]
            for product in low_stock_products:
                status = 'OUT OF STOCK' if product.stock_quantity == 0 else 'LOW STOCK'
                data.append([
                    product.name[:25],
                    product.sku,
                    str(product.stock_quantity),
                    str(product.min_stock_level),
                    status
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        else:
            story.append(Paragraph("All products are adequately stocked.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        return story

    def _generate_financial_analytics(self, daily_report):
        """Generate financial analytics section"""
        story = []
        story.append(Paragraph("Financial Analytics", self.styles['Heading2']))
        
        # Get 7-day trend
        end_date = daily_report.date
        start_date = end_date - timedelta(days=6)
        
        trend_data = DailyReport.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')
        
        if trend_data.count() > 1:
            # Create trend table
            data = [['Date', 'Sales', 'Expenses', 'Profit', 'Transactions']]
            for report in trend_data:
                profit = report.total_sales - report.total_expenses
                data.append([
                    report.date.strftime('%m/%d'),
                    f'${report.total_sales:,.0f}',
                    f'${report.total_expenses:,.0f}',
                    f'${profit:,.0f}',
                    str(report.total_transactions)
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        story.append(Spacer(1, 20))
        return story

    def _generate_expense_breakdown(self, report_date):
        """Generate expense breakdown section"""
        story = []
        story.append(Paragraph("Expense Breakdown", self.styles['Heading2']))
        
        # Get expenses by category
        expenses = Expense.objects.filter(date=report_date).values(
            'category__name'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('-total_amount')
        
        if expenses:
            data = [['Category', 'Amount', 'Percentage']]
            total_expenses = sum(expense['total_amount'] for expense in expenses)
            
            for expense in expenses:
                percentage = (expense['total_amount'] / total_expenses * 100) if total_expenses > 0 else 0
                data.append([
                    expense['category__name'],
                    f"${expense['total_amount']:,.2f}",
                    f"{percentage:.1f}%"
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        else:
            story.append(Paragraph("No expenses recorded for this date.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        return story

    def _generate_payment_method_chart(self, daily_report):
        """Generate payment method pie chart"""
        story = []
        story.append(Paragraph("Payment Method Distribution", self.styles['Heading2']))
        
        # Create pie chart data
        payment_data = [
            ('Cash', float(daily_report.cash_sales)),
            ('Card', float(daily_report.card_sales)),
            ('Mobile', float(daily_report.mobile_sales))
        ]
        
        # Filter out zero values
        payment_data = [(label, value) for label, value in payment_data if value > 0]
        
        if payment_data:
            # Create matplotlib pie chart
            fig, ax = plt.subplots(figsize=(8, 6))
            labels, values = zip(*payment_data)
            
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title('Payment Method Distribution')
            
            # Save chart as image
            chart_path = os.path.join(settings.MEDIA_ROOT, 'temp', f'payment_chart_{daily_report.date}.png')
            os.makedirs(os.path.dirname(chart_path), exist_ok=True)
            plt.savefig(chart_path, bbox_inches='tight', dpi=150)
            plt.close()
            
            # Add chart to PDF
            img = Image(chart_path, width=400, height=300)
            story.append(img)
            
            # Clean up temp file
            try:
                os.remove(chart_path)
            except:
                pass
        
        story.append(Spacer(1, 20))
        return story

    def _generate_hourly_sales_trend(self, report_date):
        """Generate hourly sales trend"""
        story = []
        story.append(Paragraph("Hourly Sales Trend", self.styles['Heading2']))
        
        # Get hourly sales data
        from django.db.models import Extract
        hourly_sales = Sale.objects.filter(
            created_at__date=report_date
        ).extra(
            select={'hour': "EXTRACT(hour FROM created_at)"}
        ).values('hour').annotate(
            total_sales=Sum('total_amount'),
            transaction_count=Count('id')
        ).order_by('hour')
        
        if hourly_sales:
            data = [['Hour', 'Sales', 'Transactions', 'Avg Sale']]
            for hour_data in hourly_sales:
                hour = int(hour_data['hour'])
                avg_sale = hour_data['total_sales'] / hour_data['transaction_count'] if hour_data['transaction_count'] > 0 else 0
                data.append([
                    f"{hour:02d}:00",
                    f"${hour_data['total_sales']:,.2f}",
                    str(hour_data['transaction_count']),
                    f"${avg_sale:.2f}"
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        story.append(Spacer(1, 20))
        return story

    def _generate_category_performance(self, report_date):
        """Generate category performance section"""
        story = []
        story.append(Paragraph("Category Performance", self.styles['Heading2']))
        
        # Get sales by category
        category_sales = SaleItem.objects.filter(
            sale__created_at__date=report_date
        ).values(
            'product__category__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price'),
            total_profit=Sum(models.F('total_price') - models.F('cost_price') * models.F('quantity'))
        ).order_by('-total_revenue')
        
        if category_sales:
            data = [['Category', 'Items Sold', 'Revenue', 'Profit', 'Margin']]
            for category in category_sales:
                margin = (category['total_profit'] / category['total_revenue'] * 100) if category['total_revenue'] > 0 else 0
                data.append([
                    category['product__category__name'],
                    str(category['total_quantity']),
                    f"${category['total_revenue']:,.2f}",
                    f"${category['total_profit']:,.2f}",
                    f"{margin:.1f}%"
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        story.append(Spacer(1, 20))
        return story

# # settings.py additions
# DAILY_REPORT_EMAIL = 'manager@yourcompany.com'
# BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

# # Email settings for reports
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'  # or your SMTP server
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'
# DEFAULT_FROM_EMAIL = 'your-email@gmail.com'



# Install required packages
# REQUIRED_PACKAGES = """
# # Add these to your requirements.txt
# reportlab==4.0.4
# matplotlib==3.7.2
# celery==5.3.1
# redis==4.6.0  # or your message broker
# django-celery-beat==2.5.0
# Pillow==10.0.0  # for image processing
# """

# Crontab setup (alternative to Celery)
# CRONTAB_SETUP = """
# # Add to your server's crontab (run: crontab -e)
# # Generate daily report at 11:30 PM
# 30 23 * * * /path/to/your/venv/bin/python /path/to/your/project/manage.py generate_daily_report

# # Backup database daily at 2:00 AM
# 0 2 * * * /path/to/your/venv/bin/python /path/to/your/project/manage.py backup_database

# # Weekly backup on Sundays at 3:00 AM
# 0 3 * * 0 /path/to/your/venv/bin/python /path/to/your/project/manage.py backup_database

# # Monthly backup on 1st day at 4:00 AM
# 0 4 1 * * /path/to/your/venv/bin/python /path/to/your/project/manage.py backup_database
# """