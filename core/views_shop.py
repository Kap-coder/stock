from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Shop, User
from django.db.models import Sum
from sales.models import Sale

@login_required
def shop_list(request):
    """
    Global dashboard for owners: List all their shops.
    """
    # Only for ADMIN/owners or Superusers
    if request.user.role != User.Role.ADMIN:
        return redirect('dashboard')
        
    shops = Shop.objects.filter(owner=request.user)
    
    # Calculate stats for each shop
    shops_data = []
    for s in shops:
        sales_today = Sale.objects.filter(shop=s).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        shops_data.append({
            'shop': s,
            'sales_today': sales_today,
            'is_current': request.user.shop == s
        })
        
    return render(request, 'core/shop_list.html', {'shops_data': shops_data})

@login_required
def shop_add(request):
    """
    Add a new shop (Enterprise).
    """
    # Need to check if user plan allows multiple shops? 
    # For now, let's assume if they can access this, they can add.
    # Or restrict to PRO? The user said "ceci en mode pro".
    
    # We should check if at least one shop is PRO? or User is PRO?
    # Current model puts plan on Shop. So we can check the *current* shop plan?
    # Or maybe the "owner" needs a subscription.
    # User Request: "mettre un onglet pour ajouter entreprise ... ceci en mode pro"
    # This implies if the CURRENT shop is Pro, they can add more?
    # Or if the USER is a "Pro Owner".
    
    # Let's enforce: Current shop must be PRO to add another.
    if not request.user.shop.is_pro:
         return render(request, 'finance/upgrade.html')

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        
        # Create new shop with FREE plan by default? Or inherit?
        # Let's make it FREE initially, they can upgrade.
        shop = Shop.objects.create(name=name, owner=request.user, plan=Shop.Plan.FREE, phone=phone)
        
        messages.success(request, f"Boutique {name} créée avec succès !")
        return redirect('shop_list')
        
    return render(request, 'core/shop_form.html')

@login_required
def shop_switch(request, shop_id):
    """
    Switch the user's current context to another shop they own.
    """
    shop = get_object_or_404(Shop, id=shop_id, owner=request.user)
    
    request.user.shop = shop
    request.user.save()
    
    messages.success(request, f"Vous êtes maintenant sur : {shop.name}")
    return redirect('dashboard')
