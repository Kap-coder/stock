from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Category
from .serializers import ProductSerializer # Or use a Django Form

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
        price = request.POST.get('selling_price')
        purchase_price = request.POST.get('purchase_price') or 0
        qty = request.POST.get('quantity')
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

        Product.objects.create(
            shop=shop,
            name=name,
            selling_price=price,
            purchase_price=purchase_price,
            quantity=qty,
            category=category
        )
        return redirect('product_list')
    
    categories = Category.objects.filter(shop=request.user.shop) if request.user.shop.is_pro else []
    return render(request, 'inventory/product_form.html', {'categories': categories})

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
