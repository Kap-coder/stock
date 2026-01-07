"""
URL configuration for shop_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse, Http404
import os

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import UserViewSet, ShopViewSet
from inventory.views import ProductViewSet, CategoryViewSet, StockMovementViewSet
from sales.views import SaleViewSet, InvoiceViewSet
from finance.views import ExpenseViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'shops', ShopViewSet, basename='shop')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'stock-movements', StockMovementViewSet, basename='stockmovement')
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    # Expose service worker at site root so it can have origin-wide scope
    path('sw.js', lambda request: FileResponse(open(os.path.join(settings.BASE_DIR, 'static', 'sw.js'), 'rb'), content_type='application/javascript')),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('', include('core.urls')),
    # path('sales/', include('sales.urls')), # Removed because core/urls redirects to dashboard, but let's keep specific app urls if they have unique prefixes. sales.urls has 'pos/' and 'invoices/' which are unique.
    # Note: we should prefix them to avoid collisions if any.
    path('sales/', include('sales.urls')), 
    path('inventory/', include('inventory.urls')),
    path('finance/', include('finance.urls')),
    path('taxes/', include('taxes.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
