from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from inventory.models import Product
from .models import Invoice

@login_required
def pos_view(request):
    products = Product.objects.filter(shop=request.user.shop)[:20]
    return render(request, 'sales/pos.html', {'products': products})

@login_required
def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(shop=request.user.shop, name__icontains=query)[:10]
    return render(request, 'sales/partials/product_results.html', {'products': products})

@login_required
def invoice_list(request):
    invoices = Invoice.objects.filter(sale__shop=request.user.shop).select_related('sale').order_by('-created_at')
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        invoices = invoices.filter(created_at__date__gte=start_date)
    if end_date:
        invoices = invoices.filter(created_at__date__lte=end_date)
    
    from django.db.models import Sum
    total_sales = invoices.aggregate(Sum('sale__total_amount'))['sale__total_amount__sum'] or 0
        
    return render(request, 'sales/invoice_list.html', {'invoices': invoices, 'total_sales': total_sales})

@login_required
def sale_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, sale__shop=request.user.shop)
    return render(request, 'sales/sale_detail.html', {'invoice': invoice, 'sale': invoice.sale})
