from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def taxes_dashboard(request):
    shop = request.user.shop
    if not shop.is_pro_plus:
        return render(request, 'finance/upgrade_pro_plus.html') # Need to create this or reuse upgrade.html with context
    
    return render(request, 'taxes/dashboard.html')
