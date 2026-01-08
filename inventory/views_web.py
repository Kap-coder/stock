from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Category
from .serializers import ProductSerializer # Or use a Django Form
from django.http import HttpResponseForbidden

@login_required
def product_list(request):
    products = Product.objects.filter(shop=request.user.shop)
    categories = Category.objects.filter(shop=request.user.shop) if request.user.shop.is_pro else []

    # Search
    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    # Category Filter
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # Low Stock Filter
    if request.GET.get('low_stock'):
        from django.db.models import F
        products = products.filter(quantity__lte=F('alert_threshold'))
    
    context = {
        'products': products, 
        'categories': categories
    }
    return render(request, 'inventory/product_list.html', context)

@login_required
def product_add(request):
    if request.method == 'POST':
        # Simple manual form handling for speed, or use Django Forms
        name = request.POST.get('name')
        price = request.POST.get('selling_price') or 0
        purchase_price = request.POST.get('purchase_price') or 0
        qty = request.POST.get('quantity') or 0
        category_id = request.POST.get('category')
        
        # ... validation ...
        
        # Check limit
        shop = request.user.shop
        if shop.products.count() >= shop.product_limit:
             # handle error
             pass

        category = None
        if shop.is_pro and category_id:
            category = Category.objects.filter(id=category_id, shop=shop).first()

        # Ensure numeric types where appropriate and provide a default for package_price
        try:
            qty_val = int(qty)
        except Exception:
            qty_val = 0

        # package_price column exists in DB and is required in some migrations/instances;
        # set to 0 by default to avoid NOT NULL errors.
        Product.objects.create(
            shop=shop,
            name=name,
            selling_price=price,
            purchase_price=purchase_price,
            package_price=0,
            quantity=qty_val,
            category=category
        )
        # Redirect to the exact inventory products route so offline SW has the cached URL
        return redirect('/inventory/products/')
    
    categories = Category.objects.filter(shop=request.user.shop) if request.user.shop.is_pro else []
    return render(request, 'inventory/product_form.html', {'categories': categories})


@login_required
def product_detail(request, pk):
    shop = request.user.shop
    product = get_object_or_404(Product, pk=pk, shop=shop)
    return render(request, 'inventory/product_detail.html', {'product': product})


@login_required
def product_edit(request, pk):
    shop = request.user.shop
    product = get_object_or_404(Product, pk=pk, shop=shop)
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('selling_price') or product.selling_price
        purchase_price = request.POST.get('purchase_price') or product.purchase_price
        qty = request.POST.get('quantity') or product.quantity
        category_id = request.POST.get('category')

        try:
            qty_val = int(qty)
        except Exception:
            qty_val = product.quantity

        category = None
        if shop.is_pro and category_id:
            category = Category.objects.filter(id=category_id, shop=shop).first()

        product.name = name
        product.selling_price = price
        product.purchase_price = purchase_price
        product.quantity = qty_val
        product.category = category
        product.save()
        return redirect('/inventory/products/')

    categories = Category.objects.filter(shop=shop) if shop.is_pro else []
    return render(request, 'inventory/product_form.html', {'categories': categories, 'product': product})


@login_required
def product_delete(request, pk):
    shop = request.user.shop
    product = get_object_or_404(Product, pk=pk, shop=shop)
    if request.method == 'POST':
        product.delete()
        return redirect('/inventory/products/')
    return HttpResponseForbidden()

@login_required
def category_list(request):
    shop = request.user.shop
    if not shop.is_pro:
         return render(request, 'finance/upgrade.html') # Reusing generic upgrade page for now
    
    categories = Category.objects.filter(shop=shop)
    return render(request, 'inventory/category_list.html', {'categories': categories})

@login_required
def category_add(request):
    shop = request.user.shop
    if not shop.is_pro:
         return render(request, 'finance/upgrade.html')

    if request.method == "POST":
        name = request.POST.get('name')
        Category.objects.create(shop=shop, name=name)
        return redirect('category_list')
        
    return render(request, 'inventory/category_form.html')
