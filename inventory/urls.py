from django.urls import path
from . import views_web

urlpatterns = [
    path('products/', views_web.product_list, name='product_list'),
    path('products/add/', views_web.product_add, name='product_add'),
    path('products/<int:pk>/', views_web.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views_web.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views_web.product_delete, name='product_delete'),
    path('categories/', views_web.category_list, name='category_list'),
    path('categories/add/', views_web.category_add, name='category_add'),
]
