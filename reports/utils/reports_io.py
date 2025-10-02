from django.template.loader import render_to_string
from weasyprint import HTML
from io import BytesIO
from dashboard.models import Sale, SaelItem, Product
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Sum

def generate_sales_summary_pdf(start_date, end_date):
    """Reports dashboard"""
    today = date.today()

    # Sales summary for different periods
    periods = {
        'Today': today,
        'Yesterday': today - timedelta(days=1),
        'This Week': today - timedelta(days=today.weekday()),
        'Last Week': today - timedelta(days=today.weekday() + 7),
        'This Month': today.replace(day=1),
        'Last Month': (today.replace(day=1) - timedelta(days=1)).replace(day=1),
    }
    
    sales_summary = {}
    for period, start_date in periods.items():
        if period in ['yesterday', 'last_week', 'last_month']:
            if period == 'yesterday':
                end_date = start_date
            elif period == 'last_week':
                end_date = start_date + timedelta(days=6)
            else:  # last_month
                next_month = start_date.replace(day=28) + timedelta(days=4)
                end_date = next_month - timedelta(days=next_month.day)
            
            sales = Sale.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).aggregate(
                total=Sum('total_amount'),
                count=Count('id')
            )
        else:
            sales = Sale.objects.filter(
                created_at__date__gte=start_date
            ).aggregate(
                total=Sum('total_amount'),
                count=Count('id')
            )
        
        sales_summary[period] = {
            'total': sales['total'] or 0,
            'count': sales['count'] or 0
        }

        html_string = render_to_string("dashboard/reports/sales_summary.html", {
            "sales_summary": sales_summary
        })

        buffer = BytesIO()

        HTML(string=html_string).write_pdf(target=buffer)
        buffer.seek(0)
        return buffer