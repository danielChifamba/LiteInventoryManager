from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, Avg
from dahboard.models import *


def dashboard_analytics():
    """Enhanced dashboard with expense analytics"""
    today = date.today()
    
    # Get today's metrics
    today_sales = Sale.objects.filter(created_at__date=today).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    today_expenses = Expense.objects.filter(date=today).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Calculate today's profit
    today_sale_items = SaleItem.objects.filter(sale__created_at__date=today)
    today_gross_profit = sum(item.get_profit() for item in today_sale_items)
    today_net_profit = today_gross_profit - (today_expenses['total'] or 0)
    
    # Get this month's metrics
    month_start = today.replace(day=1)
    month_sales = Sale.objects.filter(created_at__date__gte=month_start).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    month_expenses = Expense.objects.filter(date__gte=month_start).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Calculate month's profit
    month_sale_items = SaleItem.objects.filter(sale__created_at__date__gte=month_start)
    month_gross_profit = sum(item.get_profit() for item in month_sale_items)
    month_net_profit = month_gross_profit - (month_expenses['total'] or 0)
    
    # Low stock products
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        is_active=True
    ).count()
    
    # Recent sales
    recent_sales = Sale.objects.select_related('cashier__user').order_by('-created_at')[:10]
    
    # Recent expenses
    recent_expenses = Expense.objects.select_related('category', 'created_by').order_by('-created_at')[:5]
    
    # Top selling products this month
    top_products = Product.objects.filter(
        saleitem__sale__created_at__date__gte=month_start
    ).annotate(
        total_sold=Sum('saleitem__quantity'),
        revenue=Sum('saleitem__total_price')
    ).order_by('-total_sold')[:5]
    
    # Top expense categories this month
    top_expense_categories = ExpenseCategory.objects.annotate(
        total_amount=Sum('expense__amount', filter=Q(expense__date__gte=month_start)),
        expense_count=Count('expense', filter=Q(expense__date__gte=month_start))
    ).filter(total_amount__gt=0).order_by('-total_amount')[:5]
    
    # Recent alerts
    recent_alerts = Alert.objects.filter(is_read=False).order_by('-created_at')[:5]
    
    # Financial ratios
    month_revenue = month_sales['total'] or 0
    month_total_expenses = month_expenses['total'] or 0
    profit_margin = (month_net_profit / month_revenue * 100) if month_revenue > 0 else 0
    expense_ratio = (month_total_expenses / month_revenue * 100) if month_revenue > 0 else 0
    
    context = {
        'today_sales': today_sales['total'] or 0,
        'today_transactions': today_sales['count'] or 0,
        'today_expenses': today_expenses['total'] or 0,
        'today_net_profit': today_net_profit,
        'month_sales': month_sales['total'] or 0,
        'month_transactions': month_sales['count'] or 0,
        'month_expenses': month_expenses['total'] or 0,
        'month_net_profit': month_net_profit,
        'low_stock_count': low_stock_products,
        'recent_sales': recent_sales,
        'recent_expenses': recent_expenses,
        'top_products': top_products,
        'top_expense_categories': top_expense_categories,
        'recent_alerts': recent_alerts,
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_categories': Category.objects.filter(is_active=True).count(),
        'total_cashiers': Cashier.objects.filter(is_active=True).count(),
        'profit_margin': profit_margin,
        'expense_ratio': expense_ratio,
    }
    
    return render(request, 'dashboard/dashboard.html', context)