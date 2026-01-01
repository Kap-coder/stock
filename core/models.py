from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        MANAGER = 'MANAGER', _('Manager')
        CASHIER = 'CASHIER', _('Caissier')
        ACCOUNTANT = 'ACCOUNTANT', _('Comptable')

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Shop(models.Model):
    class Plan(models.TextChoices):
        FREE = 'FREE', _('Gratuit')
        MEDIUM = 'MEDIUM', _('Medium')
        PRO = 'PRO', _('Pro')
        PRO_PLUS = 'PRO_PLUS', _('Pro+')

    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_shops')
    created_at = models.DateTimeField(auto_now_add=True)
    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.FREE)
    
    # Address, Phone, etc. can be added here
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def product_limit(self):
        if self.plan == self.Plan.FREE:
            return 50
        return float('inf')
    
    @property
    def has_advanced_accounting(self):
        return self.plan in [self.Plan.MEDIUM, self.Plan.PRO, self.Plan.PRO_PLUS]

    @property
    def has_professional_invoice(self):
        return self.plan in [self.Plan.MEDIUM, self.Plan.PRO, self.Plan.PRO_PLUS]

    @property
    def is_pro(self):
        return self.plan in [self.Plan.PRO, self.Plan.PRO_PLUS]

    @property
    def is_pro_plus(self):
        return self.plan == self.Plan.PRO_PLUS

class SubscriptionPlan(models.Model):
    code = models.CharField(max_length=20, choices=Shop.Plan.choices, unique=True)
    name = models.CharField(max_length=50) # e.g. "Pack Démarrage", "Business"
    price = models.IntegerField(default=0)
    old_price = models.IntegerField(null=True, blank=True)
    features = models.TextField(help_text="Une fonctionnalité par ligne")
    is_popular = models.BooleanField(default=False)
    whatsapp_number = models.CharField(max_length=20, default="22500000000")
    
    def __str__(self):
        return self.name

    @property
    def features_list(self):
        return [f.strip() for f in self.features.split('\n') if f.strip()]
