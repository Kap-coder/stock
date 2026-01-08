from django.db import models
from core.models import Shop, User
from inventory.models import Product
from django.utils.translation import gettext_lazy as _

class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', _('Espèces')
        MOBILE_MONEY = 'MOMO', _('Mobile Money')
        BANK_TRANSFER = 'BANK', _('Virement Bancaire')
        CARD = 'CARD', _('Carte Bancaire')

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sales')
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales')
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)

    def __str__(self):
        return f"Sale #{self.id} - {self.total_amount}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200) # Snapshot in case product is deleted/renamed
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at the moment of sale
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.price
        # Update product stock on save? Or separate service? 
        # Better to do it in a service/view to handle atomicity and validation.
        super().save(*args, **kwargs)

class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = 'CASH', _('Espèces')
        MOBILE_MONEY = 'MOMO', _('Mobile Money')

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=10, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True, null=True) # For Mobile Money
    created_at = models.DateTimeField(auto_now_add=True)

class Invoice(models.Model):
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name='invoice')
    number = models.CharField(max_length=50, unique=True)
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ActionLog(models.Model):
    class ActionChoices(models.TextChoices):
        SALE_CREATED = 'SALE_CREATED', 'Sale created'
        SALE_DELETED = 'SALE_DELETED', 'Sale deleted'
        INVOICE_PDF_GENERATED = 'INVOICE_PDF_GENERATED', 'Invoice PDF generated'
        ITEM_ADDED = 'ITEM_ADDED', 'Item added'
        ITEM_UPDATED = 'ITEM_UPDATED', 'Item updated'

    shop = models.ForeignKey('core.Shop', on_delete=models.CASCADE, related_name='action_logs')
    user = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ActionChoices.choices)
    object_type = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.created_at}] {self.get_action_display()} ({self.object_type}#{self.object_id})"
