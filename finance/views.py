from rest_framework import viewsets
from .models import Expense, Transaction
from .serializers import ExpenseSerializer, TransactionSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        user = self.request.user
        if user.shop:
            return Expense.objects.filter(shop=user.shop)
        return Expense.objects.none()

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop, created_by=self.request.user)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.shop:
            # Check if shop is PRO? Logic can be in permission or here.
            # For now, return list.
            return Transaction.objects.filter(shop=user.shop)
        return Transaction.objects.none()
