from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from decimal import Decimal

import json
import logging
from django.db.models import Q, F
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.db import transaction

from django.core.exceptions import ValidationError

from settings.models import Business, ReceiptSettings, General
from dashboard.models import Cashier, Product, Sale, SaleItem, StockMovement, Category, DailyReport, Alert

logger = logging.getLogger(__name__)

# Create your views here.
@login_required
def pos_view(request):
    business = Business.objects.first()
    general = General.objects.first()
    cashier = Cashier.objects.get(user=request.user)
    
    context = {
        'business': business,
        'general': general,
        'profile': cashier,
        'receiptSettings': ReceiptSettings.objects.first(),
    }
    return render(request, 'POS/pos_update.html', context)

@login_required
def get_categories(request):
    try:
        categories = Category.objects.filter(is_active=True)
        data = []
        for category in categories:
            data.append({
                'cid': category.cid,
                'name': category.name,
                'description': category.description,
                'item_count': category.get_total_products(),
            })
        return JsonResponse({
            'success': True,
            'data': data,
        })
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error fetching categories'
        }, status=500)

@login_required
def get_products(request):
    """Get products with optional category filter"""
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

@csrf_exempt
@login_required
@require_http_methods(['POST'])
def complete_sale(request):
    """Complete a sale transaction"""
    settings = ReceiptSettings.objects.first()
    general = General.objects.first()
    try:
        data = json.loads(request.body)        
        # Validate required fields
        required_fields = ['payment_method', 'subtotal', 'total_amount', 'items']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }, status=400)

        
        # Validate payment
        total_amount = Decimal(str(data['total_amount']))
        # amount_paid = Decimal(str(data['amount_paid']))
        
        # if amount_paid < total_amount:
        #     return JsonResponse({
        #         'success': False,
        #         'message': 'Insufficient payment amount'
        #     }, status=400)
        
        # Get or create cashier for current user
        cashier = Cashier.objects.get(user=request.user)
        
        with transaction.atomic():
            # Create sale record
            sale = Sale.objects.create(
                cashier=cashier,
                payment_method=data['payment_method'],
                subtotal=Decimal(str(data['subtotal'])),
                tax_amount=Decimal(str(data.get('tax_amount', 0))),
                discount_amount=Decimal(str(data.get('discount_amount', 0))),
                total_amount=total_amount,
                # amount_paid=amount_paid,
                # change_amount=amount_paid - total_amount,
                notes=data.get('notes', '')
            )
            
            # Process sale items
            sale_items = []
            stock_movements = []
            
            for item_data in data['items']:
                try:
                    product = Product.objects.select_for_update().get(sku=item_data['sku'], is_active=True
                    )
                    quantity = int(item_data['quantity'])
                    unit_price = Decimal(str(item_data['unit_price']))
                    cost_price = Decimal(str(item_data.get('cost_price', product.cost_price)))
                    
                    # Check stock availability
                    if product.stock_quantity < quantity:
                        raise ValueError(f'Insufficient stock for {product.name}')
                    
                    # Create sale item
                    sale_item = SaleItem(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=unit_price * quantity,
                        cost_price=cost_price
                    )
                    sale_items.append(sale_item)
                    # Update product stock
                    product.stock_quantity = F('stock_quantity') - quantity
                    product.save(update_fields=['stock_quantity'])
                    
                    # Refresh product to get updated stock
                    product.refresh_from_db()
                    
                    # Create stock movement record
                    stock_movement = StockMovement(
                        product=product,
                        movement_type='out',
                        quantity=-quantity,  # Negative for stock out
                        unit_cost=cost_price,
                        reference=f'{sale.sale_id}',
                        notes=f'Sale to customer',
                        created_by=request.user
                    )
                    stock_movements.append(stock_movement)
                    
                    # Check for low stock alert
                    if product.is_low_stock() and product.stock_quantity > 0:
                        Alert.objects.create(
                            alert_type='low_stock',
                            title=f'Low Stock Alert: {product.name}',
                            message=f'{product.name} is running low. Current stock: {product.stock_quantity}'
                        )
                    elif product.is_out_of_stock():
                        Alert.objects.create(
                            alert_type='out_of_stock',
                            title=f'Out of Stock: {product.name}',
                            message=f'{product.name} is now out of stock.'
                        )
                    
                
                except Product.DoesNotExist:
                    raise ValueError(f'Product not found: {item_data["sku"]}')
            
            # Bulk create sale items and stock movements
            SaleItem.objects.bulk_create(sale_items)
            StockMovement.objects.bulk_create(stock_movements)
            
            # Update daily report
            update_daily_report(sale)

            sales = []
            for item in sale_items:
                itemVal = {
                    'product_name': item.product.name,
                    'sku': item.product.sku,
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'total_price': str(item.total_price),
                    'cost_price': str(item.cost_price),
                }
                sales.append(itemVal)

            subtotal = round(sale.subtotal, 2)
            total = round(sale.total_amount, 2)
            tax = round(sale.discount_amount, 2)
            
            # Prepare response data
            sale_data = {
                'sale_id': sale.sale_id,
                'payment_method': sale.payment_method,
                'subtotal': str(subtotal),
                'tax_amount': str(sale.tax_amount),
                'discount_amount': str(sale.discount_amount),
                'total_amount': str(total),
                # 'amount_paid': str(sale.amount_paid),
                # 'change_amount': str(sale.change_amount),
                'created_at': sale.created_at.strftime(general.date_format),
                'cashier_name': sale.cashier.user.get_full_name(),
                'items': sales,

                # settings for the receipt display
                'showThanks': settings.show_thank_you_note,
                'thanksNote': settings.thank_you_note,
                'showName': settings.show_cashier_name,
                'showTime': settings.show_sales_time,
                'showLogo': settings.show_logo,
            }
            
            return JsonResponse({
                'success': True,
                'message': 'Sale completed successfully',
                'sale': sale_data
            })
    
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error completing sale: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error processing sale'
        }, status=500)

def update_daily_report(sale):
    """Update or create daily report with sale data"""
    try:
        report, created = DailyReport.objects.get_or_create(
            date=sale.created_at.date(),
            defaults={
                'total_sales': Decimal('0'),
                'total_transactions': 0,
                'cash_sales': Decimal('0'),
                'card_sales': Decimal('0'),
                'mobile_sales': Decimal('0'),
            }
        )
        
        # Update totals
        report.total_sales = F('total_sales') + sale.total_amount
        report.total_transactions = F('total_transactions') + 1
        
        # Update payment method totals
        if sale.payment_method == 'cash':
            report.cash_sales = F('cash_sales') + sale.total_amount
        elif sale.payment_method == 'card':
            report.card_sales = F('card_sales') + sale.total_amount
        elif sale.payment_method == 'mobile':
            report.mobile_sales = F('mobile_sales') + sale.total_amount
        
        report.save()
        
        # Update top selling product (simplified - could be more sophisticated)
        # This would typically be done in a background task
        
    except Exception as e:
        logger.error(f"Error updating daily report: {e}")

@login_required
def get_sales_summary(request):
    """Get sales summary for today"""
    try:
        from datetime import date
        today = date.today()
        
        # Get today's sales
        today_sales = Sale.objects.filter(created_at__date=today)
        total_sales = sum(sale.total_amount for sale in today_sales)
        total_transactions = today_sales.count()
        
        # Payment method breakdown
        cash_sales = sum(sale.total_amount for sale in today_sales if sale.payment_method == 'cash')
        card_sales = sum(sale.total_amount for sale in today_sales if sale.payment_method == 'card')
        mobile_sales = sum(sale.total_amount for sale in today_sales if sale.payment_method == 'mobile')
        
        # Top selling products today
        from django.db.models import Sum
        top_products = SaleItem.objects.filter(
            sale__created_at__date=today
        ).values(
            'product__name', 'product__sku'
        ).annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_qty')[:5]
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_sales': str(total_sales),
                'total_transactions': total_transactions,
                'cash_sales': str(cash_sales),
                'card_sales': str(card_sales),
                'mobile_sales': str(mobile_sales),
                'top_products': list(top_products),
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching sales summary: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error fetching sales summary'
        }, status=500)

@login_required
def get_alerts(request):
    """Get unread alerts"""
    try:
        alerts = Alert.objects.filter(is_read=False).order_by('-created_at')[:10]
        
        alert_data = [
            {
                'id': alert.id,
                'alert_type': alert.alert_type,
                'title': alert.title,
                'message': alert.message,
                'created_at': alert.created_at.isoformat(),
            }
            for alert in alerts
        ]
        
        return JsonResponse({
            'success': True,
            'data': alert_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error fetching alerts'
        }, status=500)

@login_required
def search_products(request):
    """Search products by name or SKU"""
    try:
        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({
                'success': True,
                'data': []
            })
        
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query),
            is_active=True
        ).order_by('name')[:10]  # Limit to 10 results
        
        product_data = []
        for product in products:
            product_data.append({
                'sku': product.sku,
                'name': product.name,
                'selling_price': str(product.selling_price),
                'cost_price': str(product.cost_price),
                'stock_quantity': product.stock_quantity,
                'category_name': product.category.name,
            })
        
        return JsonResponse({
            'success': True,
            'data': product_data
        })
    
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error searching products'
        }, status=500)

@login_required
def get_product_info(request, sku):
    try:
        product = Product.objects.get(sku=sku, is_active=True)
        data = {
            'id': product.id,
            'name': product.name,
            'selling_price': product.selling_price,
            'cost_price': product.cost_price,
            'stock_quantity': product.stock_quantity,
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

@login_required
@csrf_exempt
def process_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            with transaction.atomic():
                sale = Sale.objects.create(
                    cashier=data['cashier_id'],
                    payment_method=data['payment_method'],
                    subtotal=Decimal(str(data.get['subtotal'])),
                    tax_amount=Decimal(str(data.get('tax_amount', 0))),
                    discount_amount=Decimal(str(data.get('discount_amount', 0))),
                    total_amount=Decimal(str(data.get['total_amount'])),
                    amount_paid=Decimal(str(data.get['amount_paid'])),
                    change_amount=Decimal(str(data.get('amount_paid'))),
                    notes=data.get('notes', '')
                )

                for item_data in data['items']:
                    product = Product.objects.get(sku=item_data['sku'])

                    if product.stock_quantity < item_data['quantity']:
                        raise ValidationError(f'Insufficient stock for {product.name}')

                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=item_data['quantity'],
                        unit_price=Decimal(str(item_data['unit_price'])),
                        total_price=Decimal(str(item_data['total_price'])),
                        cost_price=product.cost_price
                    )

                    StockMovement.objects.create(
                        product=product,
                        movement_type='out',
                        quantity=item_data['quantity'],
                        unit_cost=product.cost_price,
                        reference=f'Sale {sale.sale_id}',
                        created_by=request.user
                    )

                    return JsonResponse({
                        'success': True,
                        'sale_id': sale.sale_id,
                        'message': 'Sale proccessed successfully'
                    })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    return JsonResponse({ 'error': 'Invalid request' }, status=400)