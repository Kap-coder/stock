from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Shop, SubscriptionPlan

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'code', 'is_popular')
    list_editable = ('price', 'is_popular')

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'shop', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'shop')
    fieldsets = UserAdmin.fieldsets + (
        ('Shop Info', {'fields': ('role', 'shop')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Shop Info', {'fields': ('role', 'shop')}),
    )

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'plan', 'created_at', 'product_count')
    list_filter = ('plan', 'created_at')
    search_fields = ('name', 'owner__username')
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Produits'

admin.site.register(User, CustomUserAdmin)
