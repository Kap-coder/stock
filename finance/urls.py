from django.urls import path
from . import views_web, views_stats, views_loans, views_export

urlpatterns = [
    path('dashboard/', views_web.accounting_dashboard, name='accounting_dashboard'),
    path('expenses/', views_web.expense_list, name='expense_list'),
    path('expenses/add/', views_web.expense_add, name='expense_add'),
    path('statistics/', views_stats.statistics_view, name='statistics'),
    
    # Loans (Medium)
    path('loans/', views_loans.loan_list, name='loan_list'),
    path('loans/add/', views_loans.loan_add, name='loan_add'),
    path('loans/<int:loan_id>/repay/', views_loans.loan_repay, name='loan_repay'),
    
    # Export (Pro)
    path('export/pdf/', views_export.export_accounting_pdf, name='export_accounting_pdf'),
]
