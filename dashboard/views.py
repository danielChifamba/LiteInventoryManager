from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F, Avg
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from datetime import datetime, timedelta, date
from .models import *
from b_auth.models import UserSession, User

from decimal import Decimal

import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.db import transaction

from django.core.exceptions import ValidationError
from datetime import date
import logging

from .forms import *

from settings.models import Business, AdminUser, General
import os
import tempfile

from .utils.product_io import import_products_from_excel, export_products_to_excel
# from .utils.reports_io import generate_sales_summary_pdf

from django.core.management import call_command

# User = get_user_model()
logger = logging.getLogger(__name__)

# ######################################################## #
# ######################################################## #
@login_required
def dashboard_view(request):
    business = Business.objects.first()
    general = General.objects.first()
    user = AdminUser.objects.get(user=request.user)
    today = date.today()

    # today metrics
    today_sales = Sale.objects.filter(created_at__date=today).aggregate(total=Sum('total_amount'), count=Count('id'))

    # month metrics
    month_start = today.replace(day=1)
    month_sales = Sale.objects.filter(created_at__date__gte=month_start).aggregate(total=Sum('total_amount'), count=Count('id'))

    # low stock products
    low_stock_products = Product.objects.filter(stock_quantity__lte=F('min_stock_level'), is_active=True).count()

    # recent sales
    recent_sales = Sale.objects.select_related('cashier__user').order_by('-created_at')[:5]

    # top selling this month
    top_products = Product.objects.filter(saleitem__sale__created_at__date__gte=month_start).annotate(total_sold=Sum('saleitem__quantity'), revenue=Sum('saleitem__total_price')).order_by('-total_sold')[:5]

    today_expenses = Expense.objects.filter(date=today).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )

    month_expenses = Expense.objects.filter(date__gte=month_start).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )

    # Calculate today's profit
    today_sale_items = SaleItem.objects.filter(sale__created_at__date=today)
    today_gross_profit = sum(item.get_profit() for item in today_sale_items)
    today_net_profit = today_gross_profit - (today_expenses['total'] or 0)

    # Calculate month's profit
    month_sale_items = SaleItem.objects.filter(sale__created_at__date__gte=month_start)
    month_gross_profit = sum(item.get_profit() for item in month_sale_items)
    month_net_profit = month_gross_profit - (month_expenses['total'] or 0)

    # Financial ratios
    month_revenue = month_sales['total'] or 0
    month_total_expenses = month_expenses['total'] or 0
    profit_margin = (month_net_profit / month_revenue * 100) if month_revenue > 0 else 0

    context = {
        'today_sales': today_sales['total'] or 0,
        'today_transactions': today_sales['count'] or 0,
        'today_expenses': today_expenses['total'] or 0,
        'today_net_profit': today_net_profit,
        'profit_margin': profit_margin,
        'recent_sales': recent_sales,
        'top_products': top_products,
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_categories': Category.objects.filter(is_active=True).count(),

        'total_cashiers': Cashier.objects.filter(is_active=True).count(),
        'month_sales': month_sales['total'] or 0,
        'month_transactions': month_sales['count'] or 0,

        'business': business,
        'profile': user,
        'general': general,
    }

    return render(request, 'dashboard/dashboard.html', context)
# ######################################################## #
# ######################################################## #
@login_required
def products_view(request):
    business = Business.objects.first()
    general = General.objects.first()
    user = AdminUser.objects.get(user=request.user)

    products = Product.objects.filter(is_active=True)
    create = ProductCreateForm()
    edit = ProductEditForm()
    context = {
        'products': products,
        'form': create,
        'editForm': edit,
        'business': business,
        'profile': user,

        'general': general,
    }
    return render(request, 'dashboard/products.html', context)
# ############### #
@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductCreateForm(request.POST)
        if form.is_valid():
            form.save()
            product = form.save(commit=False)
            # create initial stock movement
            StockMovement.objects.create(product=product, movement_type='in', quantity=product.stock_quantity, unit_cost=product.cost_price, reference='Initial Stock', created_by=request.user)
            product.save()
            messages.success(request, f'Yay! {product.name} is now live in your inventory.')
        else:
            messages.error(request, f'Oops! something went wrong while adding the product. Please try again.')
    return redirect('dashboard:adminProducts')

@login_required
def update_product_view(request, sku):
    product = get_object_or_404(Product, sku=sku)
    if request.method == 'POST':
        form = ProductEditForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'All good! {product.name} has been updated.')
        else:
            messages.error(request, f'Oops! something went wrong while updating {product.name}. Please try again.')
    return redirect('dashboard:adminProducts')
# ############### #
@login_required
def delete_product_view(request, sku):
    if request.method == 'POST':
        product = get_object_or_404(Product, sku=sku)
        if product.is_active:
            product.is_active = False
            product.save()
            messages.success(request, f'Bye-bye {product.name}! its been removed from your inventory.')
    return redirect('dashboard:adminProducts')
# ######################################################## #

@login_required
def expenses_view(request):
    business = Business.objects.first()
    general = General.objects.first()
    user = AdminUser.objects.get(user=request.user)

    expenses = Expense.objects.filter(is_active=True)

    create = CreateExpensesForm()

    context = {
        'business': business,
        'profile': user,
        'general': general,

        'expenses': expenses,
        'form': create,
    }

    return render(request, 'dashboard/expenses.html', context)

@login_required
def delete_expense(request, id):
    # delete expense
    if request.method == 'POST':
        expense = get_object_or_404(Expense, expense_id=id)
        if expense.is_active:
            expense.is_active = False
            expense.save()
            messages.success(request, f'Gone, {expense.expense_id} has been removed.')
    return redirect('dashboard:adminExpenses')

@login_required
def create_expenses(request):
    if request.method == 'POST':
        form = CreateExpensesForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            # Create alert for high expenses
            if expense.amount > 1000:  # Configurable threshold
                Alert.objects.create(alert_type='high_expense', title=f'High Expense Alert',message=f'Expense of ${expense.amount} was recorded for {expense.description}')
            messages.success(request, f'Expense has been logged! Keep track of those expenses.')
        else:
            messages.error(request, 'Oops! Invalid input. Please try again.')

    return redirect('dashboard:adminExpenses')

@login_required
def update_expense_view(request, id):
    if request.method == 'POST':
        expense = get_object_or_404(Expense, expense_id=id)
        form = CreateExpensesForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f"Expense with ID: {expense.expense_id} updated.You're on top of it!")
    return redirect('dashboard:adminExpenses')

# ######################################################## #
@login_required
def categories_view(request):
    business = Business.objects.first()
    general = General.objects.first()
    user = AdminUser.objects.get(user=request.user)

    edit = CategoryEditForm()
    form = CategoryCreateForm()

    context = {
        'categories': Category.objects.filter(is_active=True),
        'form': form,
        'editForm': edit,
        'business': business,
        'profile': user,

        'general': general,
    }

    return render(request, 'dashboard/categories.html', context)
# ############### #
@login_required
def product_category_create(request):
    if request.method == 'POST':
        form = CategoryCreateForm(request.POST)
        if form.is_valid():
            catName = form.cleaned_data['name']
            if Category.objects.filter(name=catName):
                messages.info(request, f'Hmm... {catName} already exists. Try a different name.')
            else:
                form.save()
                messages.success(request, f'Category {catName} is all set up and ready to go.')
        else:
            messages.info(request, f'Invalid entry while adding category. Please try again.')
    return redirect('dashboard:adminCategories')

@login_required
def update_category_view(request, cid):
    category = get_object_or_404(Category, cid=cid)
    if request.method == 'POST':
        form = CategoryEditForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Nice work! {category.name} has been updated.')
        else:
            messages.error(request, f'Invalid entry while updating category {category.name}. Please try again.')
    return redirect('dashboard:adminCategories')
# ############### #
@login_required
def delete_category_view(request, cid):
    if request.method == 'POST':
        category = Category.objects.get(cid=cid)
        if category.get_total_products() >= 1:
            messages.info(request, f'Hey! category {category.name} has an item.')
            return redirect('dashboard:adminCategories')
        if category.is_active:
            category.is_active = False
            category.save()
            messages.success(request, f'Gone! {category.name} has been removed.')
    return redirect('dashboard:adminCategories')
# ######################################################## #
# ######################################################## #
@login_required
def cashiers_view(request):
    business = Business.objects.first()
    general = General.objects.first()
    user = AdminUser.objects.get(user=request.user)

    create = CashierCreateForm()
    edit = CashierEditForm()
    context = {
        'cashiers': Cashier.objects.filter(is_active=True),
        'sessions': UserSession.objects.all(),
        'form': create,
        'editForm': edit,
        'business': business,
        'profile': user,

        'general': general,
    }
    return render(request, 'dashboard/cashiers.html', context)
# ############### #
@login_required
def create_cashier(request):
    if request.method == 'POST':
        create = CashierCreateForm(request.POST)
        if create.is_valid():
            username = create.cleaned_data['username']
            first_name = create.cleaned_data['first_name']
            last_name = create.cleaned_data['last_name']
            email = create.cleaned_data['email']
            phone_number = create.cleaned_data['phone_number']
            password = create.cleaned_data['password']
            confirm_password = create.cleaned_data['confirm_password']

            if password == confirm_password:
                user = User.objects.create_cashier(username=username, email=email, password=password, first_name=first_name, last_name=last_name, phone_number=phone_number)
                Cashier.objects.create(user=user)
                messages.success(request, f'Cashier : {user.get_full_name()} was added successfully.')
                UserSession.objects.create(user=user)
            else:
                messages.error(request, f'Passwords do not match, Please try again')
        else:
            messages.error(request, 'Invalid entry while adding cashier. Try again.')

    return redirect('dashboard:adminCashiers')

@login_required
def update_cashier_view(request, id):
    if request.method == 'POST':
        cashier = Cashier.objects.get(cashier_id=id)
        user = User.objects.get(id=cashier.user.id)
        form = CashierEditForm(request.POST)
        if form.is_valid():
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.phone_number = form.cleaned_data['phone_number']
            user.email = form.cleaned_data['email']
            user.save()
            messages.success(request, f'Cashier: {cashier.user.get_full_name()} was successfully updated.')
        else:
            messages.error(request, f'Oops! invalid entry while updating cashier. Please try again.')
    return redirect('dashboard:adminCashiers')
# ############### #
@login_required
def delete_cashier_view(request, id):
    if request.method == 'POST':
        cashier = Cashier.objects.get(cashier_id=id)
        if cashier.is_active:
            cashier.is_active = False
            cashier.save()
            messages.success(request, f'Cashier: {cashier.user.get_full_name()} successfully deleted.')
    return redirect('dashboard:adminCashiers')
# ######################################################## #
# ######################################################## #

@login_required
def sales_filter(request):
    try:
        products = Product.objects.filter(is_active=True)
        
        # Filter by category if provided
        category_id = request.GET.get('category')
        if category_id:
            products = products.filter(category__cid=category_id)
        
        # Search query
        search = request.GET.get('search')
        if search:
            products = products.filter(
                Q(name__icontains=search) | 
                Q(sku__icontains=search)
            )
        
        # Order by name
        products = products.order_by('name')
        
        product_data = []
        for product in products:
            product_data.append({
                'sku': product.sku,
                'name': product.name,
                'description': product.description,
                'selling_price': str(product.selling_price),
                'cost_price': str(product.cost_price),
                'stock_quantity': product.stock_quantity,
                'min_stock_level': product.min_stock_level,
                'category_name': product.category.name,
                'category_id': product.category.cid,
                'is_low_stock': product.is_low_stock(),
                'is_out_of_stock': product.is_out_of_stock(),
            })
        
        return JsonResponse({
            'success': True,
            'data': product_data
        })
    
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error fetching products'
        }, status=500)
# ######################################################## #
# ######################################################## #

@login_required
def export_products(request):
    if Product.objects.all():
        buffer = export_products_to_excel()
        return FileResponse(buffer, as_attachment=True, filename='products_export.xlsx')
    else:
        messages.info(request, 'Export failed. Product list is empty')
        return redirect('dashboard:adminProducts')

@login_required
def import_products(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            result = import_products_from_excel(request.FILES['file'], request.user)

            messages.success(request, f"{result['success']} products imported, {result['failed']} failed.")

            for e in result['errors']:
                messages.warning(request, e)
        except Exception as e:
            messages.error(request, f'Import failed: {e}')
    
    return redirect('dashboard:adminProducts')

def check_alerts(request):
    unread_alerts = Alert.objects.filter(is_read=False)
    if unread_alerts.exists():
        alert = unread_alerts.first()
        # alert.is_read = True
        # alert.save()
        return render(request, 'components/partials/alert_toast_p.html', {'alert': alert})
    return render(request, 'empty.html')

def mark_as_read(request, pk):
    alert = Alert.objects.get(pk=pk)
    alert.is_read = True
    alert.save()
    return JsonResponse({'success': True})
