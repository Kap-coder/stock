from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Customer, Loan

@login_required
def loan_list(request):
    shop = request.user.shop

    # Check permissions
    if request.user.role not in ['ADMIN', 'MANAGER', 'ACCOUNTANT']:
        return render(request, 'finance/upgrade.html') # Or 403

    # Check Medium plan
    if not shop.has_advanced_accounting: 
        return render(request, 'finance/upgrade.html')

    # Split into Loans (Receivables) and Debts (Payables)
    loans = Loan.objects.filter(shop=shop, loan_type=Loan.LoanType.LOAN).select_related('customer').order_by('-created_at')
    debts = Loan.objects.filter(shop=shop, loan_type=Loan.LoanType.DEBT).select_related('customer').order_by('-created_at')
    
    return render(request, 'finance/loan_list.html', {
        'loans': loans,
        'debts': debts
    })

@login_required
def loan_add(request):
    shop = request.user.shop
    if not shop.has_advanced_accounting:
        return render(request, 'finance/upgrade.html')

    # Get type from GET (default to LOAN)
    loan_type = request.GET.get('type', Loan.LoanType.LOAN)
    
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date') or None
        loan_type_post = request.POST.get('loan_type', Loan.LoanType.LOAN)
        
        # Get or Create Customer
        customer, created = Customer.objects.get_or_create(
            shop=shop, 
            name=customer_name,
            defaults={'phone': request.POST.get('customer_phone', '')}
        )
        
        Loan.objects.create(
            shop=shop,
            customer=customer,
            loan_type=loan_type_post,
            amount=amount,
            description=description,
            due_date=due_date
        )
        
        msg = "Prêt enregistré." if loan_type_post == Loan.LoanType.LOAN else "Dette enregistrée."
        messages.success(request, msg)
        return redirect('loan_list')
        
    return render(request, 'finance/loan_form.html', {'loan_type': loan_type})

@login_required
def loan_repay(request, loan_id):
    shop = request.user.shop
    loan = get_object_or_404(Loan, id=loan_id, shop=shop)
    
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))
        loan.amount_paid = float(loan.amount_paid) + amount
        
        if loan.amount_paid >= loan.amount:
            loan.status = Loan.Status.PAID
            loan.amount_paid = loan.amount # Cap at max
        else:
            loan.status = Loan.Status.PARTIAL
            
        loan.save()
        messages.success(request, f"Remboursement de {amount} FCFA enregistré.")
        return redirect('loan_list')
    
    return redirect('loan_list')
