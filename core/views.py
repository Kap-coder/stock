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
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

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

@require_POST
def api_sync(request):
    """Endpoint pour recevoir une liste d'opérations (ex: ventes) envoyées depuis la PWA.
    Attends JSON: { "operations": [ {"type":"sale", "payload": {...} }, ... ] }
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    ops = data.get('operations') if isinstance(data, dict) else data
    if not isinstance(ops, list):
        return JsonResponse({'error': 'operations must be a list'}, status=400)

    results = []
    errors = []

    from sales.models import SaleItem
    from inventory.models import Product, StockMovement

    for op in ops:
        try:
            if op.get('type') == 'sale':
                payload = op.get('payload') or {}
                shop = request.user.shop
                if not shop:
                    errors.append({'op': op, 'error': 'User has no shop'})
                    continue

                with transaction.atomic():
                    sale = Sale.objects.create(shop=shop, cashier=request.user)
                    total = 0
                    items = payload.get('items', [])
                    if not items:
                        raise ValueError('Aucun article dans la vente.')

                    for it in items:
                        product_id = it.get('product')
                        quantity = int(it.get('quantity', 0))
                        price = it.get('price')
                        product = None
                        product_name = it.get('product_name')

                        if product_id:
                            product = Product.objects.filter(id=product_id, shop=shop).first()
                            if not product:
                                raise ValueError(f"Produit {product_id} introuvable ou hors shop.")
                            if product.quantity < quantity:
                                raise ValueError(f"Stock insuffisant pour '{product.name}'.")
                            if price is None:
                                price = product.selling_price
                            product_name = product.name

                        if price is None:
                            price = 0

                        subtotal = quantity * float(price)
                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            product_name=product_name or 'Vente libre',
                            quantity=quantity,
                            price=price,
                            subtotal=subtotal
                        )
                        total += subtotal

                        if product:
                            StockMovement.objects.create(
                                product=product,
                                quantity=quantity,
                                movement_type=StockMovement.MovementType.OUT,
                                reason=f"Vente #{sale.id}"
                            )
                            product.quantity -= quantity
                            product.save()

                    sale.total_amount = total
                    sale.save()
                    results.append({'type': 'sale', 'id': sale.id})
            else:
                errors.append({'op': op, 'error': 'Unknown op type'})
        except Exception as e:
            errors.append({'op': op, 'error': str(e)})

    return JsonResponse({'created': results, 'errors': errors})

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('onboarding')
