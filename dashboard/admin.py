from django.contrib import admin
from .models import *

# Register your models here.
class CategoryDisplay(admin.ModelAdmin):
    list_display = ('cid', 'name', 'description')

class ProductDisplay(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'cost_price', 'selling_price')
    
admin.site.register(Category, CategoryDisplay)
admin.site.register(Product, ProductDisplay)
admin.site.register(StockMovement)
admin.site.register(Cashier)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(Expense)
admin.site.register(ExpenseCategory)
admin.site.register(DailyReport)
admin.site.register(Alert)