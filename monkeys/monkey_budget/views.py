from django.shortcuts import render, get_object_or_404, redirect
from .models import MoneyAccount, Transaction, SubTransaction
from .forms import *

# Create your views here.
# TODO - brak informacji o id użytkownika, jest wpisane na sztywno do zmiany po dodaniu możliwości logowania
def dashboard(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    context = {'accounts': all_accounts}
    return render(request, 'account/base.html', context)

def show_money_account(request, account_id):
    chosen_account = get_object_or_404(MoneyAccount, pk=account_id)
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    context = {'account': chosen_account, 'accounts': all_accounts}
    return render(request, 'account/show_account.html', context)

def add_money_account(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    context = {'accounts': all_accounts}
    return render(request, 'account/add_account.html', context)

def edit_money_account(request):
    return render(request, 'account/edit_account.html')

def delete_money_account(request, account_id):
    account = get_object_or_404(MoneyAccount, id=account_id)
    account.delete()
    return redirect('dashboard')

#zaklepuje poniższe linijki pod transakcje

def transaction_create_or_update(request, account_id, pk=None):
    if pk:
        transaction = get_object_or_404(Transaction, pk=pk)
    else:
        transaction = Transaction()

    if request.metho == "POST":
        form = TransactionForm(request.POST, instance=transaction)
        formset = SubTransactionFormset(request.POST, instance=transaction)

        if form.is_valid() and formset.is_valid():
            sub_form_data = formset.cleaned_data
            active_subs = [f for f in sub_form_data if not f.get('DELETE', False) and f.get('amount') is not None]

        if not active_subs:
            formset.add_error(None, "Transakcja musi posiadać co najmniej jedną subtransakcję.")
        else:
            transaction = form.save(commit=False) # zapisuje transakcję bez total i balance_after_transaction

            formset.save() # zapisuje subtransakcje

            total_sum = sum(sub.amount for sub in transaction.sub_transaction.all())
            transaction.total = total_sum

            current_account_balance = transaction.account.current_balance
            if transaction.transaction_direction == 'IN':
                transaction.balance_after_transaction = current_account_balance + total_sum
            else:
                transaction.balance_after_transaction = current_account_balance - total_sum

            transaction.account.current_balance = transaction.balance_after_transaction
            transaction.account.save()