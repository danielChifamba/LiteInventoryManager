from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy

from dashboard.models import Product, Category
from dashboard.forms import ProductEditForm, CategoryEditForm

@login_required
def get_product(request, sku):
    if request.htmx:
        product = get_object_or_404(Product, sku=sku)
        form = ProductEditForm(instance=product)
        context = {
            'editForm': form,
            'product': product,
        }
        return render(request, 'components/partials/product_update_p.html', context)

@login_required
def get_product_delete(request, sku):
    if request.htmx:
        product = get_object_or_404(Product, sku=sku)
        context = {
            'product': product,
        }
        return render(request, 'components/partials/product_delete_p.html', context)

# #####################################################
# #####################################################
# #####################################################
@login_required
def get_product_category(request, cid):
    if request.htmx:
        category = get_object_or_404(Category, cid=cid)
        form = CategoryEditForm(instance=category)
        context = {
            'editForm': form,
            'category': category,
        }
        return render(request, 'components/partials/product_category_update_p.html', context)

@login_required
def get_product_category_delete(request, cid):
    if request.htmx:
        category = get_object_or_404(Category, cid=cid)
        context = {
            'category': category,
        }
        return render(request, 'components/partials/product_category_delete_p.html', context)
