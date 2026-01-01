from django.contrib import admin
from .models import Expense, Transaction

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'category', 'shop', 'date', 'created_by')
    list_filter = ('shop', 'category', 'date')
    date_hierarchy = 'date'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'transaction_type', 'shop', 'date')
    list_filter = ('shop', 'transaction_type', 'date')
