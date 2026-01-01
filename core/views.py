from rest_framework import viewsets
from .models import User, Shop
from .serializers import UserSerializer, ShopSerializer
from rest_framework.permissions import IsAuthenticated

# Web Views
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from sales.models import Sale

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        if user.shop:
            # Check if shop is PRO? Logic can be in permission or here.
            # For now, return list.
            return User.objects.filter(shop=user.shop) # Keeping original model for UserViewSet
        return User.objects.filter(id=user.id) # Keeping original logic for UserViewSet

class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Shop.objects.all()
        # If user is part of a shop, maybe they should see it?
        # But for managing shops, usually owner only.
        return Shop.objects.filter(owner=user)

@login_required
def dashboard(request):
    shop = request.user.shop
    if not shop:
        return render(request, 'core/no_shop.html') # todo
    
    today = timezone.now().date()
    today_sales = Sale.objects.filter(shop=shop, created_at__date=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Recent sales
    recent_sales = Sale.objects.filter(shop=shop).order_by('-created_at')[:5]

    context = {
        'shop': shop,
        'product_count': shop.products.count(),
        'today_sales': today_sales,
        'recent_sales': recent_sales,
        # Add more stats here
    }
    return render(request, 'core/dashboard.html', context)

def login_view(request):
    from django.contrib.auth import authenticate, login
    from django.contrib import messages
    
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        shop_name = request.POST.get('shop_name')
        
        # Authenticate directly with username
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Enforce shop name for non-admin users (Employees)
            if user.role != User.Role.ADMIN:
                if not shop_name:
                    messages.error(request, "Le nom de la boutique est requis pour les employés.")
                    return render(request, 'core/login.html')
                
                # Verify shop association
                if not user.shop or user.shop.name.lower() != shop_name.lower():
                    messages.error(request, "Ce nom d'utilisateur n'est pas associé à cette boutique.")
                    return render(request, 'core/login.html')
            
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
             
    return render(request, 'core/login.html')

def register(request):
    if request.method == 'POST':
        # Simple registration for MVP
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        shop_name = request.POST.get('shop_name')
        
        if User.objects.filter(username=username).exists():
             from django.contrib import messages
             messages.error(request, "Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.")
             return render(request, 'core/register.html')
        
        # Create User
        user = User.objects.create_user(username=username, email=email, password=password, role=User.Role.ADMIN)
        
        # Create Shop
        shop = Shop.objects.create(name=shop_name, owner=user)
        user.shop = shop
        user.save()
        
        from django.contrib.auth import login
        login(request, user)
        return redirect('dashboard')
        
    return render(request, 'core/register.html')

def onboarding(request):
    return render(request, 'core/onboarding.html')

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('onboarding')
