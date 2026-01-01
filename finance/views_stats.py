from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale, SaleItem

@login_required
def statistics_view(request):
    shop = request.user.shop
    
    # Check permissions (Admin, Manager, Accountant)
    if request.user.role not in ['ADMIN', 'MANAGER', 'ACCOUNTANT']:
        return render(request, 'core/403.html') # Need to create 403 or redirect
    
    # Check subscription (Medium+)
    if not shop.has_advanced_accounting:
        return render(request, 'finance/upgrade.html')

    # Date Range (Last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Sales per day
    daily_sales = Sale.objects.filter(
        shop=shop, 
        created_at__gte=start_date
    ).annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('day')
    
    # Prepare data for Chart.js
    dates = [item['day'].strftime('%d/%m') for item in daily_sales]
    totals = [float(item['total']) for item in daily_sales]
    
    total_rev = sum(totals)
    total_count = sum(item['count'] for item in daily_sales)
    avg_basket = total_rev / total_count if total_count > 0 else 0
    
    # Top Products
    top_products = SaleItem.objects.filter(
        sale__shop=shop,
        sale__created_at__gte=start_date
    ).values(
        'product_name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_revenue')[:5]
    
    # Gross Margin (Estimated)
    # We need product purchase price.
    margin_query = SaleItem.objects.filter(
        sale__shop=shop,
        sale__created_at__gte=start_date
    ).annotate(
        cost=F('quantity') * F('product__purchase_price')
    ).aggregate(
        gp=Sum(F('subtotal') - F('cost'))
    )
    gross_margin = margin_query['gp'] or 0
    
    context = {
        'dates': dates,
        'totals': totals,
        'top_products': top_products,
        'total_revenue_30d': total_rev,
        'total_sales_count': total_count,
        'avg_basket': avg_basket,
        'gross_margin': gross_margin,
    }
    
    return render(request, 'finance/statistics.html', context)
