from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_view, name='adminReport'),
    path('ajax/sales_report/filter', views.date_filter, name='dateFilter'),
    path('ajax/analytics/filter', views.date_analytics_filter, name='dateAnalyticsFilter'),
    path('ajax/receipt/<str:sale_id>', views.get_receipt, name='receipt_info'),

    path('reports/download/comprehensive/', views.download_comprehensive_report, name='downloadComprehensiveReport'),
    path('reports/download/daily/', views.download_daily_report_pdf, name='downloadDailyReport'),
    path('reports/manual-daily-report/', views.manual_daily_report, name='manualDailyReport'),
]