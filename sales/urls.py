from django.urls import path
from . import views_web

urlpatterns = [
    path('pos/', views_web.pos_view, name='pos'),
    path('invoices/', views_web.invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', views_web.sale_detail, name='sale_detail'),
    path('invoices/<int:invoice_id>/delete/', views_web.sale_delete, name='sale_delete'),
    path('actions/', views_web.action_log, name='action_log'),
    path('invoices/<int:invoice_id>/receipt/', views_web.sale_receipt, name='sale_receipt'),
    path('products/search/', views_web.search_products, name='product_search'),
]
