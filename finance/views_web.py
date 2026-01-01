from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from .models import Expense
from sales.models import Sale
from core.models import Shop

@login_required
def accounting_dashboard(request):
    shop = request.user.shop
    
    # Check permissions
    if request.user.role not in ['ADMIN', 'MANAGER', 'ACCOUNTANT']:
        return redirect('dashboard') # Redirect to general dashboard if not allowed

    # Check Plan
    if shop.plan == Shop.Plan.FREE:
        return render(request, 'finance/upgrade.html') # Teaser

    today = timezone.now().date()
    
    # Calculate Gross Profit (Sales - COGS)
    from sales.models import SaleItem
    from django.db.models import F

    # Gross Profit = Sum(Selling Price - Purchase Price)
    # Note: simple version using current product purchase price.
    gross_profit = SaleItem.objects.filter(sale__shop=shop).annotate(
        cost=F('quantity') * F('product__purchase_price')
    ).aggregate(
        gp=Sum(F('subtotal') - F('cost'))
    )['gp'] or 0
    
    # Calculate Net Profit = Gross Profit - Expenses
    total_sales = Sale.objects.filter(shop=shop).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_expenses = Expense.objects.filter(shop=shop).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Expense Breakdown by Category
    expense_breakdown = Expense.objects.filter(shop=shop).values('category').annotate(total=Sum('amount')).order_by('-total')
    
    net_profit = gross_profit - total_expenses
    
    context = {
        'total_sales': total_sales,
        'gross_profit': gross_profit,
        'cogs': total_sales - gross_profit, # Cost of Goods Sold
        'total_expenses': total_expenses,
        'expense_breakdown': expense_breakdown,
        'profit': net_profit, 
        'is_pro': shop.plan == Shop.Plan.PRO,
    }
    return render(request, 'finance/dashboard.html', context)

@login_required
def expense_list(request):
    expenses = Expense.objects.filter(shop=request.user.shop).order_by('-date')
    return render(request, 'finance/expense_list.html', {'expenses': expenses})

@login_required
def expense_add(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        category = request.POST.get('category')
        description = request.POST.get('description')
        date = request.POST.get('date')
        
        Expense.objects.create(
            shop=request.user.shop,
            created_by=request.user,
            amount=amount,
            category=category,
            description=description,
            date=date
        )
        return redirect('expense_list')
    return render(request, 'finance/expense_form.html')
