from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDay, TruncHour, TruncMonth
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale, SaleItem
from inventory.models import Product

@login_required
def statistics_view(request):
    shop = request.user.shop
    
    # Check permissions (Admin, Manager, Accountant)
    if request.user.role not in ['ADMIN', 'MANAGER', 'ACCOUNTANT']:
        return render(request, 'core/403.html') # Need to create 403 or redirect
    
    # Check subscription (Medium+)
    if not shop.has_advanced_accounting:
        return render(request, 'finance/upgrade.html')

    now = timezone.now()

    # Recent periods
    period_30d_start = now - timedelta(days=30)
    period_7d_start = now - timedelta(days=7)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    qs_all = Sale.objects.filter(shop=shop)
    qs_30d = qs_all.filter(created_at__gte=period_30d_start)
    qs_7d = qs_all.filter(created_at__gte=period_7d_start)
    qs_today = qs_all.filter(created_at__gte=today_start)

    # Totals
    total_rev_all = qs_all.aggregate(total=Sum('total_amount'))['total'] or 0
    total_rev_30d = qs_30d.aggregate(total=Sum('total_amount'))['total'] or 0
    total_rev_7d = qs_7d.aggregate(total=Sum('total_amount'))['total'] or 0
    total_rev_today = qs_today.aggregate(total=Sum('total_amount'))['total'] or 0

    count_all = qs_all.count()
    count_30d = qs_30d.count()
    count_7d = qs_7d.count()
    count_today = qs_today.count()

    avg_order_all = float(total_rev_all) / count_all if count_all else 0
    avg_order_30d = float(total_rev_30d) / count_30d if count_30d else 0

    # Trends: daily sales for last 30 days
    daily = qs_30d.annotate(day=TruncDay('created_at')).values('day').annotate(total=Sum('total_amount'), count=Count('id')).order_by('day')
    dates = [d['day'].strftime('%d/%m') for d in daily]
    totals = [float(d['total']) for d in daily]

    # Monthly trend last 12 months
    monthly = qs_all.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('total_amount')).order_by('month')
    months = [m['month'].strftime('%b %Y') for m in monthly]
    month_totals = [float(m['total']) for m in monthly]

    # Payments breakdown
    payments = qs_30d.values('payment_method').annotate(total=Sum('total_amount'), count=Count('id')).order_by('-total')

    # Top products (30d)
    top_products = SaleItem.objects.filter(sale__shop=shop, sale__created_at__gte=period_30d_start).values('product_name').annotate(total_qty=Sum('quantity'), total_revenue=Sum('subtotal')).order_by('-total_revenue')[:10]

    # Top cashiers
    top_cashiers = qs_30d.values('cashier__username').annotate(total=Sum('total_amount'), count=Count('id')).order_by('-total')[:10]

    # Sales by hour (last 7 days)
    hourly = qs_7d.annotate(hour=TruncHour('created_at')).values('hour').annotate(total=Sum('total_amount'), count=Count('id')).order_by('hour')

    # Inventory: low stock
    low_stock = Product.objects.filter(shop=shop, quantity__lte=F('alert_threshold')).order_by('quantity')[:20]

    context = {
        # KPIs
        'total_rev_all': total_rev_all,
        'total_rev_30d': total_rev_30d,
        'total_rev_7d': total_rev_7d,
        'total_rev_today': total_rev_today,
        'count_all': count_all,
        'count_30d': count_30d,
        'count_7d': count_7d,
        'count_today': count_today,
        'avg_order_all': avg_order_all,
        'avg_order_30d': avg_order_30d,
        # Trends
        'dates': dates,
        'totals': totals,
        'months': months,
        'month_totals': month_totals,
        'payments': payments,
        'top_products': top_products,
        'top_cashiers': top_cashiers,
        'hourly': hourly,
        'low_stock': low_stock,
    }

    return render(request, 'finance/statistics_full.html', context)
