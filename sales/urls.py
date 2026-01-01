from django.urls import path
from . import views_web

urlpatterns = [
    path('pos/', views_web.pos_view, name='pos'),
    path('invoices/', views_web.invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', views_web.sale_detail, name='sale_detail'),
    path('products/search/', views_web.search_products, name='product_search'),
]
