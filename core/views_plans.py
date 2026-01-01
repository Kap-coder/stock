from django.shortcuts import render, redirect
from .models import SubscriptionPlan
import urllib.parse

def plans_view(request):
    plans = SubscriptionPlan.objects.all().order_by('price')
    return render(request, 'core/plans.html', {'plans': plans})

def plan_subscribe(request, plan_id):
    plan = SubscriptionPlan.objects.get(id=plan_id)
    
    # WhatsApp Logic
    phone = plan.whatsapp_number
    message = f"Bonjour, je suis intéressé par le plan {plan.name} à {plan.price} FCFA."
    
    # If user is logged in, add details
    if request.user.is_authenticated:
        message += f"\nMon username: {request.user.username}"
        if request.user.shop:
             message += f"\nMa boutique: {request.user.shop.name}"
             
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
    
    return redirect(whatsapp_url)
