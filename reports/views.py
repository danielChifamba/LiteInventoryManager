from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F, Avg
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy
from datetime import datetime, timedelta, date
from b_auth.models import UserSession, User
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
import tempfile
import logging
import os

from dashboard.models import *
from .utils.reports import GeneralReport, SalesReport, InventoryReport, analytics
from settings.models import Business, AdminUser, General
from .utils.report_pdf import generate_pdf_report

# User = get_user_model()
logger = logging.getLogger(__name__)


@login_required
def report_view(request):
    business = Business.objects.first()
    general = General.objects.first()
    user = AdminUser.objects.get(user=request.user)
    total_sales = Sale.objects.all().aggregate(total=Sum('total_amount'), count=Count('id'))
    settings = {
        'business': business,
        'general': general,
        'profile': user,
        'sales': Sale.objects.all(),
        'sale_item': SaleItem.objects.all(),
        'total_sales': total_sales,
        'today': date.today().isoformat(),
    }
    date_from = request.GET.get('date_from', str(date.today().replace(day=1)))
    date_to = request.GET.get('date_to', str(date.today()))
    general = GeneralReport()
    sales = SalesReport(date_from, date_to)
    anlytics_ = analytics(date_from, date_to)
    inventory = InventoryReport()
    context = {**general, **sales, **inventory, **anlytics_, **settings}
    return render(request, 'reports/report.html', context)
# #####################

@login_required
def date_filter(request):
    business = Business.objects.first()
    general = General.objects.first()
    if request.htmx:
        date_from = request.POST['date_from']
        date_to = request.POST['date_to']
        settings = {
            'business': business,
            'general': general,
        }

        sales = SalesReport(date_from, date_to)
        context = {**sales, **settings}
        return render(request, 'components/partials/date_filter_p.html', context)

@login_required
def date_analytics_filter(request):
    business = Business.objects.first()
    general = General.objects.first()
    if request.htmx:
        date_from = request.POST['date_from']
        date_to = request.POST['date_to']
        settings = {
            'business': business,
            'general': general,
        }

        analytic = analytics(date_from, date_to)
        context = {**analytic, **settings}
        return render(request, 'components/partials/date_filter_analytics_p.html', context)

@login_required
def get_receipt(request, sale_id):
    business = Business.objects.first()
    general = General.objects.first()
    if request.htmx:
        sale = Sale.objects.get(sale_id=sale_id)
        saleItems = SaleItem.objects.filter(sale=sale)
        context = {
            'business': business,
            'general': general,
            'sale': sale,
            'sale_items': saleItems,
        }
        return render(request, 'components/partials/receipt_p.html', context)

    messages.error(request, f'Failed to get receipt {sale_id} data.')    
    return redirect('reports:adminReport')

@login_required
def download_comprehensive_report(request):
    """Download comprehensive PDF report"""
    if request.method == 'POST':
        date_from = request.POST['date_from']
        date_to = request.POST['date_to']

        try:
            datetime.strptime(date_from, '%Y-%m-%d')
            datetime.strptime(date_to, '%Y-%m-%d')
        except ValueError:
            messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
            return redirect('reports:adminReport')

        pdf_buffer = generate_pdf_report('comprehensive', date_from, date_to)
            
        # Prepare response
        business = Business.objects.first()
        filename = f"comprehensive_report_{date_from}_to_{date_to}.pdf"
        
        if business:
            filename = f"{business.business_name.replace(' ', '_')}_report_{date_from}_to_{date_to}.pdf"
        
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        messages.success(request, f'Report Generated successfully...')
        return response

    else:
        messages.error(request, f'Failed to generate report...')
        return redirect('reports:adminReport')

@login_required
def download_daily_report_pdf(request):
    """Download daily report PDF"""
    try:
        report_date = request.GET.get('date', str(date.today() - timedelta(days=1)))
        # Validate date format
        try:
            datetime.strptime(report_date, '%Y-%m-%d')
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('reports:adminReport')
        
        # Generate PDF
        pdf_buffer = generate_pdf_report('daily', report_date=report_date)
        
        # Prepare response
        business = Business.objects.first()
        filename = f"daily_report_{report_date}.pdf"
        
        if business:
            filename = f"{business.business_name.replace(' ', '_')}_daily_{report_date}.pdf"
        
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f'Daily PDF report generation failed: {e}')
        messages.error(request, f'Failed to generate daily report: {str(e)}')
        return redirect('reports:adminReport')

@login_required
def manual_daily_report(request):
    """Manually trigger daily report generation and email"""
    admin = AdminUser.objects.get(user=request.user)
    try:
        report_date = request.GET.get('date', str(date.today() - timedelta(days=1)))
        
        # Validate date
        try:
            datetime.strptime(report_date, '%Y-%m-%d')
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('reports:adminReport')

        if admin.enable_daily_reports:
            if not admin.daily_report_email:
                messages.info(request, 'No daily report email configured')
        
            # Call management command
            call_command('daily_report', date=report_date, send_email=True)
        
            messages.success(request, f'Daily report for {report_date} generated successfully.')
        else:
            messages.info(request, f'Daily Reports not enabled.')
        
    except Exception as e:
        logger.error(f'Manual daily report failed: {e}')
        messages.error(request, f'Failed to generate daily report: {str(e)}')
    
    return redirect('reports:adminReport')
