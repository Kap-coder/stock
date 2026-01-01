from django.db import models
from core.models import Shop, User
from django.utils.translation import gettext_lazy as _

class Expense(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='expenses')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=100) # Could be a model if needed
    description = models.TextField(blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"

class Transaction(models.Model):
    """
    Journal comptable pour le plan PRO.
    """
    class Type(models.TextChoices):
        CREDIT = 'CREDIT', _('Crédit')
        DEBIT = 'DEBIT', _('Débit')

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=Type.choices)
    related_document = models.CharField(max_length=100, blank=True, null=True) # e.g. "Invoice #123"

    def __str__(self):
        return f"{self.date} - {self.description} ({self.amount})"

class Customer(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Loan(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('En cours')
        PAID = 'PAID', _('Remboursé')
        PARTIAL = 'PARTIAL', _('Partiellement remboursé')

    class LoanType(models.TextChoices):
        LOAN = 'LOAN', _('Prêt (Client doit)')
        DEBT = 'DEBT', _('Dette (Boutique doit)')

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='loans')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(max_length=10, choices=LoanType.choices, default=LoanType.LOAN)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer.name} - {self.amount}"
        
    @property
    def remaining_amount(self):
        return self.amount - self.amount_paid
