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

def transaction_create_or_update(request, pk=None):
    if pk:
        transaction = get_object_or_404(Transaction, pk=pk)
    else:
        transaction = Transaction()

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        formset = SubtransactionFormSet(request.POST, instance=transaction)

        if form.is_valid() and formset.is_valid():
            transaction = form.save(commit=False)

            subtransactions = formset.save(commit=False)

            total_sum = sum(sub.amount for sub in subtransactions if sub.amount)

            transaction.total = total_sum

            account = transaction.account
            if transaction.transaction_direction == 'IN':
                transaction.balance_after_transaction = account.balance + total_sum
            else:
                transaction.balance_after_transaction = account.balance - total_sum

            account.balance = transaction.balance_after_transaction
            account.save()

            transaction.save()

            for sub in subtransactions:
                sub.main_transaction = transaction
                sub.save()

            formset.save()

            return redirect('nowa-transakcja')
    else:
        form = TransactionForm(instance=transaction)
        formset = SubtransactionFormSet(instance=transaction)

    return render(request, 'account/transaction_form.html', {
        'form': form,
        'formset': formset,
    })