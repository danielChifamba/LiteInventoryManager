from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy

from dashboard.forms import CreateExpensesForm, UpdateExpensesForm
from dashboard.models import Expense

@login_required
def get_expense(request, id):
    if request.htmx:
        expense = get_object_or_404(Expense, expense_id=id)
        form = UpdateExpensesForm(instance=expense)
        context = {
            'editForm': form,
            'expense': expense,
        }
        return render(request, 'components/partials/expense_update_p.html', context)

@login_required
def get_expense_image(request, id):
    if request.htmx:
        expense = get_object_or_404(Expense, expense_id=id)
        context = {
            'expense': expense,
        }
        return render(request, 'components/partials/expense_img_p.html', context)

@login_required
def get_expense_delete(request, id):
    if request.htmx:
        expense = get_object_or_404(Expense, expense_id=id)
        context = {
            'expense': expense,
        }
        return render(request, 'components/partials/expense_delete_p.html', context)

# #####################################################
# #####################################################
# #####################################################

