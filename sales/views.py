from rest_framework import viewsets
from .models import Sale, Invoice, Payment
from .serializers import SaleSerializer, InvoiceSerializer, PaymentSerializer

class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer

    def get_queryset(self):
        user = self.request.user
        if user.shop:
            return Sale.objects.filter(shop=user.shop)
        return Sale.objects.none()

    def perform_create(self, serializer):
        # Associate shop and cashier
        serializer.save(shop=self.request.user.shop, cashier=self.request.user)

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        user = self.request.user
        if user.shop:
            return Invoice.objects.filter(sale__shop=user.shop)
        return Invoice.objects.none()
