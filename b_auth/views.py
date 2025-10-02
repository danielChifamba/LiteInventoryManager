from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from .models import UserSession

from .forms import AdminLoginForm
from .forms import CashierLoginForm
from .forms import ResetPasswordForm

from settings.models import General

# Create your views here.
def login_view(request):
    return render(request, 'login.html')

def admin_login_view(request):
    admin = AdminLoginForm(request.POST)
    general = General.objects.first()
    context = {
        'form': admin,
        'general': general
    }

    if admin.is_valid():
        username = admin.cleaned_data['username']
        password = admin.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_cashier or user.is_super:
                messages.error(request, 'Access Denied.')
                return render(request, 'admin-login.html', context)
            else:
                login(request, user)
                return redirect('dashboard:adminDashboard')
        else:
            messages.error(request, 'Login failed. Invalid username or password.')
            return render(request, 'admin-login.html', context)
                
    return render(request, 'admin-login.html', context)

def cashier_login_view(request):
    cashier = CashierLoginForm(request.POST)
    general = General.objects.first()
    context = {
        'form': cashier,
        'general': general,
    }

    if cashier.is_valid():
        username = cashier.cleaned_data['username']
        password = cashier.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_admin or user.is_super:
                messages.error(request, 'Access Denied.')
                return render(request, 'cashier-login.html', context)
            else:
                login(request, user)
                session = get_object_or_404(UserSession, user=request.user)
                if session:
                    session.is_active = True
                    session.login_time = timezone.now()
                    session.save()
                else:
                    session.create(user=user)
                return redirect('pos:cashierPOS')
        else:
            messages.error(request, 'Login failed. Invalid username or password.')
            return render(request, 'cashier-login.html', context)

    return render(request, 'cashier-login.html', context)

@login_required
def user_logout(request):
    try:
        session = get_object_or_404(UserSession, user=request.user)
        if session:
            session.logout_time = timezone.now()
            session.is_active = False
            session.save()
    except:
        pass

    logout(request)
    return redirect('b_auth:login')

def password_reset_view(request):
    success = False
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user:
                success = True

            return render(request, 'resetPassword.html', {'success': True, 'form': form})
    else:
        form = ResetPasswordForm()
    
    return render(request, 'resetPassword.html', {'success': success, 'form': form, 'general': General.objects.first(),})