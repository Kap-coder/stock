from django.shortcuts import render, HttpResponse
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from core.models import Shop, User
from sales.models import Sale, SaleItem
from finance.models import Expense, Loan
from inventory.models import Product
from xhtml2pdf import pisa
import datetime

@login_required
def export_accounting_pdf(request):
    shop = request.user.shop
    
    # Permission Check (Admin, Manager, Accountant)
    if request.user.role not in ['ADMIN', 'MANAGER', 'ACCOUNTANT']:
        return render(request, 'core/403.html')

    # Plan Check (PRO only for full report?)
    # User asked for "uniquement en plan pro" in the prompt.
    if not shop.is_pro:
         return render(request, 'finance/upgrade.html')

    # Data Gathering
    
    # 1. P&L
    gross_profit = SaleItem.objects.filter(sale__shop=shop).annotate(
        cost=F('quantity') * F('product__purchase_price')
    ).aggregate(
        gp=Sum(F('subtotal') - F('cost'))
    )['gp'] or 0
    
    total_sales = Sale.objects.filter(shop=shop).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_expenses = Expense.objects.filter(shop=shop).aggregate(Sum('amount'))['amount__sum'] or 0
    cogs = total_sales - gross_profit
    net_profit = gross_profit - total_expenses
    
    # 2. Stock
    products = Product.objects.filter(shop=shop)
    stock_count = products.count()
    stock_quantity = products.aggregate(Sum('quantity'))['quantity__sum'] or 0
    stock_value = products.aggregate(
        val=Sum(F('quantity') * F('purchase_price'))
    )['val'] or 0
    stock_value_sell = products.aggregate(
        val=Sum(F('quantity') * F('selling_price'))
    )['val'] or 0
    
    # 3. Loans/Debts
    receivables = Loan.objects.filter(
        shop=shop, 
        loan_type=Loan.LoanType.LOAN
    ).exclude(status=Loan.Status.PAID)
    
    total_receivables = sum([l.remaining_amount for l in receivables])
    
    payables = Loan.objects.filter(
        shop=shop, 
        loan_type=Loan.LoanType.DEBT
    ).exclude(status=Loan.Status.PAID)
    
    total_payables = sum([l.remaining_amount for l in payables])
    
    context = {
        'shop': shop,
        'request': request,
        'total_sales': total_sales,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'stock_count': stock_count,
        'stock_quantity': stock_quantity,
        'stock_value': stock_value,
        'stock_value_sell': stock_value_sell,
        'total_receivables': total_receivables,
        'total_payables': total_payables,
        'balance_tiers': total_receivables - total_payables
    }
    
    template_path = 'finance/report_pdf.html'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_comptable_{datetime.date.today()}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(
       html, dest=response
    )
    
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    
    return response
