from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Count, Q, Avg, F
from datetime import datetime, timedelta
import logging

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, black, grey
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from dashboard.models import Sale, SaleItem, Product, Expense, Category, Cashier, DailyReport
from settings.models import Business, General

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#2c3e50')
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=HexColor('#34495e')
        ))

    def generate_comprehensive_report(self, date_from, date_to):
        """Generate comprehensive business report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        story = []

        # Get business info
        business = Business.objects.first()
        
        # Title
        title = f"Business Report - {date_from} to {date_to}"
        if business:
            title = f"{business.business_name} - Business Report"
        
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))

        # Report period
        period_text = f"Report Period: {date_from} to {date_to}"
        story.append(Paragraph(period_text, self.styles['Normal']))
        story.append(Spacer(1, 20))

        # Sales Summary
        story.extend(self._generate_sales_summary(date_from, date_to))
        
        # Product Performance
        story.extend(self._generate_product_performance(date_from, date_to))
        
        # Financial Summary  
        story.extend(self._generate_financial_summary(date_from, date_to))
        
        # Inventory Status
        story.extend(self._generate_inventory_status())
        
        # Expense Summary
        story.extend(self._generate_expense_summary(date_from, date_to))

        doc.build(story)
        buffer.seek(0)
        return buffer

    def _generate_sales_summary(self, date_from, date_to):
        """Generate sales summary section"""
        business = Business.objects.first()
        story = []
        story.append(Paragraph("Sales Summary", self.styles['SectionHeader']))

        # Get sales data
        sales = Sale.objects.filter(
            created_at__date__range=[date_from, date_to]
        )
        
        total_sales = sales.aggregate(
            total=Sum('total_amount'),
            count=Count('id'),
            avg=Avg('total_amount')
        )

        # Payment method breakdown
        payment_breakdown = sales.aggregate(
            cash=Sum('total_amount', filter=Q(payment_method='cash')),
            card=Sum('total_amount', filter=Q(payment_method='card')),
            mobile=Sum('total_amount', filter=Q(payment_method='mobile'))
        )

        # Sales summary table
        sales_data = [
            ['Metric', 'Value'],
            ['Total Sales', f"{business.currency_symbol}{total_sales['total'] or 0:.2f}"],
            ['Total Transactions', str(total_sales['count'] or 0)],
            ['Average Transaction', f"{business.currency_symbol}{total_sales['avg'] or 0:.2f}"],
            ['Cash Sales', f"{business.currency_symbol}{payment_breakdown['cash'] or 0:.2f}"],
            ['Card Sales', f"{business.currency_symbol}{payment_breakdown['card'] or 0:.2f}"],
            ['Mobile Sales', f"{business.currency_symbol}{payment_breakdown['mobile'] or 0:.2f}"],
        ]

        sales_table = Table(sales_data, colWidths=[3*inch, 2*inch])
        sales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(sales_table)
        story.append(Spacer(1, 20))
        return story

    def _generate_inventory_status(self):
        """Generate inventory status section"""
        story = []
        story.append(Paragraph("Inventory Status", self.styles['SectionHeader']))

        # Get inventory data
        total_products = Product.objects.filter(is_active=True).count()
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            is_active=True
        )
        out_of_stock = Product.objects.filter(
            stock_quantity=0,
            is_active=True
        ).count()

        # Inventory summary
        inventory_data = [
            ['Metric', 'Count'],
            ['Total Active Products', str(total_products)],
            ['Low Stock Products', str(low_stock_products.count())],
            ['Out of Stock Products', str(out_of_stock)],
        ]

        inventory_table = Table(inventory_data, colWidths=[3*inch, 2*inch])
        inventory_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(inventory_table)

        # Low stock products details
        if low_stock_products.exists():
            story.append(Spacer(1, 10))
            story.append(Paragraph("Low Stock Products Detail", self.styles['Normal']))
            
            low_stock_data = [['Product', 'Current Stock', 'Min Level']]
            for product in low_stock_products[:20]:  # Limit to 20 for space
                low_stock_data.append([
                    product.name[:25],
                    str(product.stock_quantity),
                    str(product.min_stock_level)
                ])

            low_stock_table = Table(low_stock_data, colWidths=[3*inch, 1*inch, 1*inch])
            low_stock_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(low_stock_table)

        story.append(Spacer(1, 20))
        return story

    def _generate_expense_summary(self, date_from, date_to):
        """Generate expense summary section"""
        business = Business.objects.first()
        story = []
        story.append(Paragraph("Expense Summary", self.styles['SectionHeader']))

        # Get expense data by category
        expenses_by_category = Expense.objects.filter(
            date__range=[date_from, date_to],
            is_active=True
        ).values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        if expenses_by_category:
            expense_data = [['Category', 'Amount', 'Count']]
            
            for expense in expenses_by_category:
                expense_data.append([
                    expense['category__name'] or 'Uncategorized',
                    f"{business.currency_symbol}{expense['total']:.2f}",
                    str(expense['count'])
                ])

            expense_table = Table(expense_data, colWidths=[3*inch, 1.5*inch, 1*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(expense_table)
        else:
            story.append(Paragraph("No expenses recorded for this period.", self.styles['Normal']))

        story.append(Spacer(1, 20))
        return story

    def generate_daily_report_pdf(self, report_date):
        """Generate daily report PDF"""
        business = Business.objects.first()
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        story = []

        business = Business.objects.first()
        
        # Title
        title = f"Daily Report - {report_date}"
        if business:
            title = f"{business.business_name} - Daily Report"
        
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))

        # Get daily report data
        try:
            daily_report = DailyReport.objects.get(date=report_date)
        except DailyReport.DoesNotExist:
            story.append(Paragraph("No daily report found for this date.", self.styles['Normal']))
            doc.build(story)
            buffer.seek(0)
            return buffer

        # Report summary
        summary_data = [
            ['Metric', 'Value'],
            ['Total Sales', f"{business.currency_symbol}{daily_report.total_sales:.2f}"],
            ['Total Transactions', str(daily_report.total_transactions)],
            ['Total Expenses', f"{business.currency_symbol}{daily_report.total_expenses:.2f}"],
            ['Cash Sales', f"{business.currency_symbol}{daily_report.cash_sales:.2f}"],
            ['Card Sales', f"{business.currency_symbol}{daily_report.card_sales:.2f}"],
            ['Mobile Sales', f"{business.currency_symbol}{daily_report.mobile_sales:.2f}"],
        ]

        if daily_report.top_selling_product:
            summary_data.append(['Top Product', daily_report.top_selling_product.name])

        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
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

        # Add daily transactions details
        story.append(Paragraph("Daily Transactions", self.styles['SectionHeader']))
        
        # Get sales for the day
        daily_sales = Sale.objects.filter(created_at__date=report_date).order_by('-created_at')[:10]
        
        if daily_sales.exists():
            transaction_data = [['Sale ID', 'Time', 'Cashier', 'Payment', 'Amount']]
            
            for sale in daily_sales:
                transaction_data.append([
                    sale.sale_id,
                    sale.created_at.strftime('%H:%M'),
                    sale.cashier.user.get_full_name()[:15] if sale.cashier else 'N/A',
                    sale.get_payment_method_display(),
                    f"{business.currency_symbol}{sale.total_amount:.2f}"
                ])

            transaction_table = Table(transaction_data, colWidths=[1.2*inch, 0.8*inch, 1.5*inch, 1*inch, 1*inch])
            transaction_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(transaction_table)
        else:
            story.append(Paragraph("No transactions recorded for this date.", self.styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer

    def _generate_product_performance(self, date_from, date_to):
        """Generate product performance section"""
        business = Business.objects.first()
        story = []
        story.append(Paragraph("Top Selling Products", self.styles['SectionHeader']))

        # Get top products
        top_products = Product.objects.filter(
            saleitem__sale__created_at__date__range=[date_from, date_to]
        ).annotate(
            total_sold=Sum('saleitem__quantity'),
            total_revenue=Sum('saleitem__total_price')
        ).order_by('-total_sold')[:10]

        if top_products:
            product_data = [['Product', 'Quantity Sold', 'Revenue']]
            
            for product in top_products:
                product_data.append([
                    product.name[:30],  # Truncate if too long
                    str(product.total_sold),
                    f"{business.currency_symbol}{product.total_revenue:.2f}"
                ])

            product_table = Table(product_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(product_table)
        else:
            story.append(Paragraph("No sales data available for this period.", self.styles['Normal']))

        story.append(Spacer(1, 20))
        return story

    def _generate_financial_summary(self, date_from, date_to):
        """Generate financial summary section"""
        business = Business.objects.first()
        story = []
        story.append(Paragraph("Financial Summary", self.styles['SectionHeader']))

        # Calculate profit
        sale_items = SaleItem.objects.filter(
            sale__created_at__date__range=[date_from, date_to]
        )
        gross_profit = sum(item.get_profit() for item in sale_items)

        # Get expenses
        expenses = Expense.objects.filter(
            date__range=[date_from, date_to],
            is_active=True
        ).aggregate(total=Sum('amount'))
        
        total_expenses = expenses['total'] or 0
        net_profit = gross_profit - total_expenses

        # Financial data
        financial_data = [
            ['Metric', 'Amount'],
            ['Gross Profit', f"{business.currency_symbol}{gross_profit:.2f}"],
            ['Total Expenses', f"{business.currency_symbol}{total_expenses:.2f}"],
            ['Net Profit', f"{business.currency_symbol}{net_profit:.2f}"],
        ]

        financial_table = Table(financial_data, colWidths=[3*inch, 2*inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1,0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(financial_table)
        story.append(Spacer(1, 20))
        return story

def generate_pdf_report(report_type, date_from=None, date_to=None, report_date=None):
    """
    Generate PDF report based on type
    
    Args:
        report_type: 'comprehensive' or 'daily'
        date_from: Start date for comprehensive report (string or date object)
        date_to: End date for comprehensive report (string or date object)
        report_date: Date for daily report (string or date object)
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
    
    generator = PDFReportGenerator()
    
    if report_type == 'comprehensive':
        if not date_from or not date_to:
            raise ValueError("date_from and date_to are required for comprehensive report")
        
        # Convert string dates to date objects if needed
        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        if isinstance(date_to, str):
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            
        return generator.generate_comprehensive_report(date_from, date_to)
    
    elif report_type == 'daily':
        if not report_date:
            raise ValueError("report_date is required for daily report")
        
        # Convert string date to date object if needed
        if isinstance(report_date, str):
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
            
        return generator.generate_daily_report_pdf(report_date)
    
    else:
        raise ValueError("Invalid report_type. Use 'comprehensive' or 'daily'")


class ReportError(Exception):
    """Custom exception for report generation errors"""
    pass


def validate_date_range(date_from, date_to):
    """Validate date range for reports"""
    if date_from > date_to:
        raise ReportError("Start date cannot be after end date")
    
    # Check if date range is too large (more than 2 years)
    if (date_to - date_from).days > 730:
        raise ReportError("Date range too large. Maximum 2 years allowed.")
    
    return True


def get_report_filename(report_type, business_name=None, date_from=None, date_to=None, report_date=None):
    """Generate appropriate filename for reports"""
    
    # Clean business name for filename
    if business_name:
        clean_name = "".join(c for c in business_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_name = clean_name.replace(' ', '_')
    else:
        clean_name = "Business_Name"
    
    if report_type == 'comprehensive':
        return f"{clean_name}_comprehensive_report_{date_from}_to_{date_to}.pdf"
    elif report_type == 'daily':
        return f"{clean_name}_daily_report_{report_date}.pdf"
    else:
        return f"{clean_name}_report.pdf"