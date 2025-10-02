from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.pos_view, name='cashierPOS'),
    
    path('api/categories', views.get_categories, name='api_categories'),
    path('api/products', views.get_products, name='api_products'),
    path('api/products/search', views.search_products, name='api_products_serach'),
    # path('api/products/detail/<str:sku>', views.pos_view, name='api_products_details'),
    path('api/sales/complete', views.complete_sale, name='api_sale_complete'),
    # path('api/sales/summary', views.pos_view, name='api_sales_summary'),
    # path('api/alerts', views.pos_view, name='api_alerts'),

]