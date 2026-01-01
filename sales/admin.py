from django.contrib import admin
from .models import Sale, SaleItem, Payment, Invoice

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'cashier', 'total_amount', 'created_at')
    list_filter = ('shop', 'created_at')
    inlines = [SaleItemInline]
    date_hierarchy = 'created_at'

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'sale', 'created_at', 'has_pdf')
    list_filter = ('created_at',)
    
    def has_pdf(self, obj):
        return bool(obj.pdf_file)
    has_pdf.boolean = True

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('sale', 'method', 'amount')
    list_filter = ('method',)
