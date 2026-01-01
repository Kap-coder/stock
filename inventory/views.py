from rest_framework import viewsets
from .models import Product, Category, StockMovement
from .serializers import ProductSerializer, CategorySerializer, StockMovementSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        user = self.request.user
        if user.shop:
            return Category.objects.filter(shop=user.shop)
        return Category.objects.none()

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop)

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user
        if user.shop:
            return Product.objects.filter(shop=user.shop)
        return Product.objects.none()

    def perform_create(self, serializer):
        shop = self.request.user.shop
        if not shop:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("User has no shop.")
        
        if shop.products.count() >= shop.product_limit:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f"Plan limit reached ({shop.product_limit} products). Upgrade to add more.")

        serializer.save(shop=shop)

class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockMovementSerializer

    def get_queryset(self):
        user = self.request.user
        if user.shop:
            return StockMovement.objects.filter(product__shop=user.shop)
        return StockMovement.objects.none()
