from dashboard.models import Sale, Product, Category, StockMovement, Expense, SaleItem, ExpenseCategory
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, Avg
from settings.models import General

# reports dashboard
def GeneralReport():
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
    
    # Top products this month
    month_start = today.replace(day=1)
    top_products = Product.objects.filter(
        saleitem__sale__created_at__date__gte=month_start
    ).annotate(
        total_sold=Sum('saleitem__quantity'),
        revenue=Sum('saleitem__total_price')
    ).order_by('-total_sold')[:5]
    
    # Low stock alerts
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        is_active=True
    ).order_by('stock_quantity')[:10]
    
    context = {
        'sales_summary': sales_summary,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
    }

    return context

def SalesReport(dte_from, dte_to):
    """Detailed sales report"""
    # Get date range from request
    date_from = dte_from
    date_to = dte_to
    
    # Sales by date
    sales_by_date = Sale.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).extra(
        select={'date': 'DATE(created_at)'}
    ).values('date').annotate(
        total_sales=Sum('total_amount'),
        total_transactions=Count('id')
    ).order_by('date')
    
    # Sales by payment method
    payment_methods = Sale.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).values('payment_method').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Sales by cashier
    cashier_performance = Sale.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).values('cashier__user__first_name', 'cashier__user__last_name').annotate(
        total_sales=Sum('total_amount'),
        total_transactions=Count('id')
    ).order_by('-total_sales')
    
    # Overall totals
    totals = Sale.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).aggregate(
        total_sales=Sum('total_amount'),
        total_transactions=Count('id'),
        avg_transaction=Avg('total_amount')
    )
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'sales_by_date': sales_by_date,
        'payment_methods': payment_methods,
        'cashier_performance': cashier_performance,
        'totals': totals,
    }

    return context

def InventoryReport():
    """Inventory report"""
    # Stock levels
    products = Product.objects.filter(is_active=True).select_related('category')
    
    # Add calculated fields
    for product in products:
        product.stock_value = product.get_stock_value()
        product.is_low_stock = product.is_low_stock()
        product.is_out_of_stock = product.is_out_of_stock()
    
    # Category-wise stock summary
    category_summary = Category.objects.filter(is_active=True).annotate(
        total_products=Count('product', filter=Q(product__is_active=True)),
        total_stock_value=Sum(
            F('product__stock_quantity') * F('product__cost_price'),
            filter=Q(product__is_active=True)
        )
    ).order_by('name')
    
    # Stock movement summary (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    movement_summary = StockMovement.objects.filter(
        created_at__date__gte=thirty_days_ago
    ).values('movement_type').annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('unit_cost'))
    ).order_by('movement_type')
    
    context = {
        'products': products,
        'category_summary': category_summary,
        'movement_summary': movement_summary,
    }

    return context

def analytics(date_from, date_to):
    """Comprehensive financial analytics including expenses"""
    general = General.objects.first()
    today = date.today()
    
    # Revenue and Sales Data
    sales_data = Sale.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).aggregate(
        total_revenue=Sum('total_amount'),
        total_transactions=Count('id'),
        avg_transaction=Avg('total_amount')
    )
    
    # Calculate total profit from sales
    sale_items = SaleItem.objects.filter(
        sale__created_at__date__gte=date_from,
        sale__created_at__date__lte=date_to
    )
    total_profit = sum(item.get_profit() for item in sale_items)
    
    # Expense Data
    expense_data = Expense.objects.filter(
        date__gte=date_from,
        date__lte=date_to
    ).aggregate(
        total_expenses=Sum('amount'),
        expense_count=Count('id'),
        avg_expense=Avg('amount')
    )
    
    # Net Profit Calculation
    net_profit = total_profit - (expense_data['total_expenses'] or 0)
    
    # Profit Margin
    revenue = sales_data['total_revenue'] or 0
    profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0
    
    # Expense by Category
    expense_by_category = ExpenseCategory.objects.annotate(
        total_amount=Sum('expense__amount', filter=Q(
            expense__date__gte=date_from,
            expense__date__lte=date_to
        )),
        expense_count=Count('expense', filter=Q(
            expense__date__gte=date_from,
            expense__date__lte=date_to
        ))
    ).filter(total_amount__gt=0).order_by('-total_amount')
    
    # Daily Financial Trend
    daily_data = []
    current_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    while current_date <= end_date:
        daily_sales = Sale.objects.filter(created_at__date=current_date).aggregate(
            revenue=Sum('total_amount')
        )['revenue'] or 0
        
        daily_expenses = Expense.objects.filter(date=current_date).aggregate(
            expenses=Sum('amount')
        )['expenses'] or 0
        
        # Calculate daily profit from sales
        daily_sale_items = SaleItem.objects.filter(sale__created_at__date=current_date)
        daily_gross_profit = sum(item.get_profit() for item in daily_sale_items)
        daily_net_profit = daily_gross_profit - daily_expenses
        
        daily_data.append({
            'date': current_date.strftime(f'{general.date_format}'),
            'revenue': float(daily_sales),
            'expenses': float(daily_expenses),
            'gross_profit': float(daily_gross_profit),
            'net_profit': float(daily_net_profit)
        })

        # print(daily_data)
        
        current_date += timedelta(days=1)
    
    # Top Expense Categories
    top_expense_categories = expense_by_category[:5]
    
    # Cash Flow Analysis
    cash_inflow = revenue
    cash_outflow = expense_data['total_expenses'] or 0
    cash_flow = cash_inflow - cash_outflow
    
    # Business Performance Metrics
    # roi = (net_profit / cash_outflow * 100) if cash_outflow > 0 else 0
    # expense_ratio = (cash_outflow / cash_inflow * 100) if cash_inflow > 0 else 0
    
    # Monthly Comparison (if viewing current month)
    current_month = today.replace(day=1)
    if date_from == str(current_month):
        last_month_start = (current_month - timedelta(days=1)).replace(day=1)
        last_month_end = current_month - timedelta(days=1)
        
        last_month_sales = Sale.objects.filter(
            created_at__date__gte=last_month_start,
            created_at__date__lte=last_month_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        last_month_expenses = Expense.objects.filter(
            date__gte=last_month_start,
            date__lte=last_month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        revenue_growth = ((revenue - last_month_sales) / last_month_sales * 100) if last_month_sales > 0 else 0
        expense_growth = ((cash_outflow - last_month_expenses) / last_month_expenses * 100) if last_month_expenses > 0 else 0
    else:
        revenue_growth = 0
        expense_growth = 0
    
    context = {
        'revenue': revenue,
        'total_profit': total_profit,
        'total_expenses': expense_data['total_expenses'] or 0,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
        'expense_count': expense_data['expense_count'] or 0,
        'avg_expense': expense_data['avg_expense'] or 0,
        'expense_by_category': expense_by_category,
        'top_expense_categories': top_expense_categories,
        'daily_data': daily_data,
        'cash_flow': cash_flow,
        'cash_outflow': cash_outflow,
        'revenue_growth': revenue_growth,
        'expense_growth': expense_growth,
    }

    return context
