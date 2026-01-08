from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from inventory.models import Product
from .models import Invoice
from .models import ActionLog
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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
    invoices_qs = Invoice.objects.filter(sale__shop=request.user.shop).select_related('sale').order_by('-created_at')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        invoices_qs = invoices_qs.filter(created_at__date__gte=start_date)
    if end_date:
        invoices_qs = invoices_qs.filter(created_at__date__lte=end_date)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(invoices_qs, 20)
    try:
        invoices = paginator.page(page)
    except PageNotAnInteger:
        invoices = paginator.page(1)
    except EmptyPage:
        invoices = paginator.page(paginator.num_pages)

    from django.db.models import Sum
    total_sales = invoices_qs.aggregate(Sum('sale__total_amount'))['sale__total_amount__sum'] or 0

    return render(request, 'sales/invoice_list.html', {'invoices': invoices, 'total_sales': total_sales, 'paginator': paginator})

@login_required
def sale_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, sale__shop=request.user.shop)
    return render(request, 'sales/sale_detail.html', {'invoice': invoice, 'sale': invoice.sale})


@login_required
def sale_delete(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    sale = invoice.sale

    # Ensure the sale belongs to the user's shop
    if sale.shop != request.user.shop:
        return HttpResponseForbidden("Accès refusé")

    # Only shop owner or shop-level admin can delete
    is_owner = (request.user == sale.shop.owner)
    is_shop_admin = (request.user.shop == sale.shop and getattr(request.user, 'role', None) == 'ADMIN')
    if not (is_owner or is_shop_admin):
        return HttpResponseForbidden("Accès refusé")

    if request.method == 'POST':
        # Log deletion before removing
        try:
            ActionLog.objects.create(
                shop=sale.shop,
                user=request.user,
                action=ActionLog.ActionChoices.SALE_DELETED,
                object_type='Sale',
                object_id=str(sale.id),
                description=f'Sale #{sale.id} deleted by {request.user.username}'
            )
        except Exception:
            pass

        sale.delete()
        messages.success(request, 'La vente a été supprimée avec succès.')
        return redirect('invoice_list')

    return render(request, 'sales/sale_confirm_delete.html', {'invoice': invoice, 'sale': sale})


@login_required
def action_log(request):
    # Only show logs for the user's shop
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    logs_qs = ActionLog.objects.filter(shop=request.user.shop).select_related('user')
    page = request.GET.get('page', 1)
    paginator = Paginator(logs_qs, 50)
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)

    return render(request, 'sales/action_log.html', {'logs': logs})


@login_required
def sale_receipt(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, sale__shop=request.user.shop)
    sale = invoice.sale
    shop = sale.shop
    return render(request, 'sales/receipt_pro.html', {'invoice': invoice, 'sale': sale, 'shop': shop})
