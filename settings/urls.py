from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.settings_view, name='settings'),
    path('business/', views.business_settings_view, name='business_settings'),
    path('general/', views.general_settings_view, name='general_settings'),
    path('profile/', views.profile_settings_view, name='profile_settings'),
    path('receipt/', views.receipt_settings_view, name='receipt_settings'),
    path('reset/', views.reset_system_view, name='reset_settings'),

    # path('settings/backup/manual/', views.manual_backup, name='manual_backup'),
    path('settings/backup/import/', views.restore_backup, name='backup_import'),

    # Manual Operations
    path('alerts/send-test/', views.send_test_alerts, name='sendTestAlerts'),
    path('backup/manual/', views.backup_database_manual, name='manualBackup'),
]