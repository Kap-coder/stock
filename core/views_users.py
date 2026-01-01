from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User

@login_required
def user_list(request):
    shop = request.user.shop
    if not shop.is_pro:
        # Redirect or show upgrade page
        return render(request, 'finance/upgrade.html')
    
    users = User.objects.filter(shop=shop)
    return render(request, 'core/user_list.html', {'users': users})

@login_required
def user_add(request):
    shop = request.user.shop
    if not shop.is_pro:
        return render(request, 'finance/upgrade.html')

    if request.method == 'POST':
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', User.Role.CASHIER) # Default to Cashier for employees
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return render(request, 'core/user_form.html')

        if User.objects.filter(phone=phone).exists():
            messages.error(request, "Ce numéro de téléphone existe déjà.")
            return render(request, 'core/user_form.html')
            
        user = User.objects.create_user(username=username, email=email, password=password, role=role, phone=phone)
        user.shop = shop
        user.save()
        messages.success(request, "Employé ajouté avec succès.")
        return redirect('user_list')
        
    return render(request, 'core/user_form.html')

@login_required
def user_edit(request, user_id):
    shop = request.user.shop
    if not shop.is_pro:
        return render(request, 'finance/upgrade.html')

    user = get_object_or_404(User, id=user_id, shop=shop)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.phone = request.POST.get('phone')
        user.email = request.POST.get('email')
        role = request.POST.get('role')
        
        # Only update password if provided
        password = request.POST.get('password')
        if password:
            user.set_password(password)
            
        user.role = role
        user.save()
        messages.success(request, "Employé modifié.")
        return redirect('user_list')
        
    return render(request, 'core/user_form.html', {'target_user': user})

@login_required
def user_delete(request, user_id):
    shop = request.user.shop
    if not shop.is_pro:
         return render(request, 'finance/upgrade.html')

    user = get_object_or_404(User, id=user_id, shop=shop)
    
    # Prevent deleting yourself
    if user == request.user:
        messages.error(request, "Impossible de supprimer votre propre compte.")
        return redirect('user_list')
        
    if request.method == 'POST':
        user.delete()
        messages.success(request, "Employé supprimé.")
        
    return redirect('user_list')
