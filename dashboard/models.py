from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from shortuuid.django_fields import ShortUUIDField
from b_auth.models import User

class timeStamp(models.Model):
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# Create your models here.
class Category(timeStamp):
    cid = ShortUUIDField(unique=True, length=4, max_length=10, prefix='CAT', alphabet='12345')
    name = models.CharField(max_length=100)
    description = models.TextField()
    # is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_total_products(self):
        return self.product_set.filter(is_active=True).count()

    def get_total_stock_value(self):
        return sum(p.get_stock_value() for p in self.product_set.filter(is_active=True))
    

class Product(timeStamp):
    sku = ShortUUIDField(unique=True, length=4, max_length=10, prefix='SKU', alphabet='1234567890')
    
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)

    min_stock_level = models.PositiveIntegerField(default=10)
    # min_stock_level = models.PositiveIntegerField(default=1000)
    # is_active = models.BooleanField(default=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.sku}"

    def get_profit_margin(self):
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return 0
    
    def get_stock_value(self):
        return self.stock_quantity * self.cost_price

    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_level

    def is_out_of_stock(self):
        return self.stock_quantity == 0

class StockMovement(timeStamp):
    MOVEMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('damaged', 'Damaged'),
    ]

    movement_id = ShortUUIDField(unique=True, length=6, max_length=10, prefix='MOV', alphabet='1234567890')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reference = models.CharField(max_length=100, blank=True, help_text='Reference number or reason')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name} - {self.movement_type} - {self.quantity}'
    

class Cashier(timeStamp):
    cashier_id = ShortUUIDField(unique=True, length=3, max_length=10, prefix='CAS', alphabet='ABCDEFG12345')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dark_mode = models.BooleanField(default=False)
    hire_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.cashier_id}"

    def get_total_sales_today(self):
        from datetime import date
        return Sale.objects.filter(Cashier=self, created_at__date=date.today()).aggregate(total=models.Sum('total_amount'))['total'] or 0


class Sale(timeStamp):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Money')
    ]

    sale_id = ShortUUIDField(unique=True, length=6, max_length=10, prefix='SAL', alphabet='1234567890')
    cashier = models.ForeignKey(Cashier, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    # amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    # change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sale {self.sale_id} - ${self.total_amount}"

    def get_profit(self):
        return sum(item.get_profit() for item in self.saleitem_set.all())
    

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def get_profit(self):
        return (self.unit_price - self.cost_price) * self.quantity

class ExpenseCategory(timeStamp):
    eid = ShortUUIDField(unique=True, length=4, max_length=15, prefix='EXP-CAT', alphabet='1234589')
    name = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        verbose_name_plural = 'Expense Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_total_expenses(self):
        return self.expense_set.filter(is_active=True).count()

    def get_total_expense_value(self):
        return sum(p.get_stock_value() for p in self.expense_set.filter(is_active=True))

class Expense(timeStamp):
    EXPENSES_CATEGORY = [
        ('Office Supplies', 'Office Supplies'),
        ('Marketing', 'Marketing'),
        ('Utilities', 'Utilities'),
        ('Transportation', 'Transportation'),
        ('Others', 'Others')
    ]
    expense_id = ShortUUIDField(unique=True, length=5, max_length=10, prefix='EXP', alphabet='1234567890')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    receipt_image = models.ImageField(upload_to='expenses/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.description} - ${self.amount}"

    def get_expense_value(self):
        return self.amount

class DailyReport(timeStamp):
    date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    card_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mobile_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    top_selling_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Report for {self.date}"

class Alert(timeStamp):
    ALERT_TYPES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('high_expense', 'High Expense'),
        ('system', 'System alert'),
    ]

    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    # created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    