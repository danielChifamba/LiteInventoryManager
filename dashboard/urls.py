from django.urls import path
from . import views

from .ajax import expenses_ajax, products_ajax

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='adminDashboard'),
    path('products/', views.products_view, name='adminProducts'),
    path('categories/products', views.categories_view, name='adminCategories'),
    path('cashiers/', views.cashiers_view, name='adminCashiers'),
    path('expenses/', views.expenses_view, name='adminExpenses'),

    path('products/create/', views.product_create, name='createProduct'),
    path('products/update/<str:sku>', views.update_product_view, name='updateProduct'),
    path('products/delete/<str:sku>', views.delete_product_view, name='deleteProduct'),

    path('expenses/create/', views.create_expenses, name='createExpense'),
    path('expenses/update/<str:id>', views.update_expense_view, name='updateExpense'),
    path('expenses/delete/<str:id>', views.delete_expense, name='deleteExpense'),

    path('categories/create', views.product_category_create, name='createCategory'),
    path('categories/update/<str:cid>', views.update_category_view, name='updateCategory'),
    path('categories/delete/<str:cid>', views.delete_category_view, name='deleteCategory'),
    
    path('cashiers/create', views.create_cashier, name='createCashier'),
    path('cashiers/update/<str:id>', views.update_cashier_view, name='updateCashier'),
    path('cashiers/delete/<str:id>', views.delete_cashier_view, name='deleteCashier'),

    path('products/import', views.import_products, name='import_products'),
    path('products/export', views.export_products, name='export_products'),
    # path('reports/sales_summary', views.download_sales_summary, name='sales_summary_pdf')

    # path('report/pdf', views.get_report, name='getReport'),

    # api calls
    path('check-alerts/', views.check_alerts, name='check_alerts'),
    path('mark_as_read/<pk>/', views.mark_as_read, name='mark_as_read'),

    path('ajax/expense/<str:id>', expenses_ajax.get_expense, name='get_expense'),
    path('ajax/expense/image/<str:id>', expenses_ajax.get_expense_image, name='get_expense_image'),
    path('ajax/expense/delete/<str:id>', expenses_ajax.get_expense_delete, name='get_expense_delete'),

    path('ajax/product/update/<str:sku>', products_ajax.get_product, name='get_product'),
    path('ajax/product/delete/<str:sku>', products_ajax.get_product_delete, name='get_product_delete'),

    path('ajax/product_category/update/<str:cid>', products_ajax.get_product_category, name='get_product_category'),
    path('ajax/product_category/delete/<str:cid>', products_ajax.get_product_category_delete, name='get_product_category_delete'),
]