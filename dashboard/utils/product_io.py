
from django.core.exceptions import ValidationError
from dashboard.models import Product, Category, StockMovement
import xlsxwriter
import xlrd
from io import BytesIO

def export_products_to_excel():
    buffer = BytesIO()

    workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
    worksheet = workbook.add_worksheet("Products")

    headers = [
        'SKU', 'Name', 'Category', 'Description' 'Cost Price', 'Selling Price', 'Stock Quantity', 'Min Stock Level'
    ]
    bold = workbook.add_format({'bold': True, 'bg_color': '#ddeeff'})

    for col, header in enumerate(headers):
        worksheet.write(0, col, header, bold)

    # products rows
    products = Product.objects.select_related('category').all()
    for row, product in enumerate(products, start=1):
        worksheet.write(row, 0, product.sku)
        worksheet.write(row, 1, product.name)
        worksheet.write(row, 2, product.category.name if product.category else '')
        worksheet.write(row, 3, product.description)
        worksheet.write(row, 4, float(product.cost_price))
        worksheet.write(row, 5, float(product.selling_price))
        worksheet.write(row, 6, product.stock_quantity)
        worksheet.write(row, 7, product.min_stock_level)

    workbook.close()
    buffer.seek(0)
    return buffer

def import_products_from_excel(file, user):
    workbook = xlrd.open_workbook(file_contents=file.read())
    sheet = workbook.sheet_by_index(0)

    headers = [sheet.cell_value(0, col).strip() for col in range(sheet.ncols)]
    required_columns = [
        'Name', 'Category', 'Description', 'Cost Price', 'Selling Price', 'Stock Quantity', 'Min Stock Level'
    ]

    header_map = {h: i for i, h in enumerate(headers)}
    for req in required_columns:
        if req not in header_map:
            raise ValidationError(f"Missing columns:{req}")

    results = {'success': 0, 'failed': 0, 'errors': []}

    for row_idx in range(1, sheet.nrows):
        try:
            row = sheet.row_values(row_idx)

            name = row[header_map['Name']]
            category_name = row[header_map['Category']]
            description = row[header_map['Description']]
            cost_price = float(row[header_map['Cost Price']])
            selling_price = float(row[header_map['Selling Price']])
            stock_quantity = int(row[header_map['Stock Quantity']])
            min_stock_level = int(row[header_map['Min Stock Level']])

            if not category_name:
                results['failed'] += 1
                results['errors'].append(f"Missing category for product '{name}'")
                continue

            category, _ = Category.objects.get_or_create(name=category_name, defaults={'description': 'Auto-created from import'})

            if Product.objects.filter(name=name):
                results['failed'] += 1
                results['errors'].append(f"Product with same name already exists: '{name}'")
                continue
            if Product.objects.filter(name=name) and Products.objects.filter(stock_quantity=0):
                results['success'] += 1
                results['success'].append(f"Product stock was updated: '{name}'")
            else:
                product = Product.objects.create(name=name, category=category, cost_price=cost_price, selling_price=selling_price, stock_quantity=stock_quantity, min_stock_level=min_stock_level, description=description)

                StockMovement.objects.create(product=product, movement_type='in', quantity=product.stock_quantity, unit_cost=product.cost_price, reference='Initial Stock', created_by=user)
                results['success'] += 1
        except Exception as e:
            results ['failed'] += 1
            results['errors'].append(f"Row {row_idx + 1}: {str(e)}")

    return results