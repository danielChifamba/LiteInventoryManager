from django.urls import path
from . import views

app_name = 'b_auth'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/admin/', views.admin_login_view, name='adminLogin'),
    path('login/cashier/', views.cashier_login_view, name='cashierLogin'),
    path('password_reset/', views.password_reset_view, name='passwordReset'),
    path('logout/', views.user_logout, name='logout'),
]