from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import MoneyAccount, Transaction, SubTransaction
from django.template.loader import render_to_string
from .forms import *

# Create your views here.
# TODO - brak informacji o id użytkownika, jest wpisane na sztywno do zmiany po dodaniu możliwości logowania
def dashboard(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    context = {'accounts': all_accounts}
    return render(request, 'account/base.html', context)

def show_money_account(request, account_id):
    account_related_transactions = Transaction.objects.filter(account_id=account_id)
    transactions_context = {'transactions': account_related_transactions}
    transactions_list_html = render_to_string('account/transactions_list_for_include.html', transactions_context)
    chosen_account = get_object_or_404(MoneyAccount, pk=account_id)
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    context = {'account': chosen_account, 'accounts': all_accounts, 'transactions_list_html': transactions_list_html}
    return render(request, 'account/show_account.html', context)

def add_money_account(request):
    if request.method == 'POST':
        form = MoneyAccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user_id = User.objects.get(pk=2)
            account.balance = Monetary.major_to_minor_unit(form.cleaned_data['balance'], account.currency)
            account.save()
            return redirect(f'/monkey-budget/konta/{account.id}')
    else:
        form = MoneyAccountForm()
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    return render(request, 'account/add_account.html', {'form': form, 'accounts': all_accounts})

def edit_money_account(request, account_id):
    chosen_account = get_object_or_404(MoneyAccount, pk=account_id)
    if request.method == 'POST':
        form = MoneyAccountForm(request.POST, instance=chosen_account)
        if form.is_valid():
            account = form.save(commit=False)
            account.balance = Monetary.major_to_minor_unit(form.cleaned_data['balance'], account.currency)
            form.save()
            return redirect(f'/monkey-budget/konta/{chosen_account.id}')
    else:
        initial_data = {
            'balance': chosen_account.balance_int_to_float() # todo sposób zapisu jest ok, tylko ładnie zastosuj funkcję
        }
        form = MoneyAccountForm(instance=chosen_account, initial=initial_data)

    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    context = {'account': chosen_account, 'accounts': all_accounts, 'form': form}
    return render(request, 'account/edit_account.html', context)

def delete_money_account(request, account_id):
    if request.method == 'POST':
        account = get_object_or_404(MoneyAccount, id=account_id)
        account.delete()
        return JsonResponse({'success': True, 'message': 'Konto zostało usunięte.'})
    return JsonResponse({'success': False, 'message': 'Nieprawidłowe żądanie.'})

#zaklepuje poniższe linijki pod transakcje

def transaction_create_or_update(request, pk=None):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    if pk:
        transaction = get_object_or_404(Transaction, pk=pk)
    else:
        transaction = Transaction()

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        form.fields.get('account').label = 'Konto'
        form.fields.get('date').label = 'Data'
        form.fields.get('transaction_direction').label = 'Rodzaj transakcji'
        form.fields.get('description').label = 'Opis'

        formset = SubTransactionFormSet(request.POST, instance=transaction)
        formset.form.base_fields.get('amount').label = 'Kwota składowa (w groszach)'
        formset.form.base_fields.get('description').label = 'Opis'

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
        form.fields.get('account').label = 'Konto'
        form.fields.get('date').label = 'Data'
        form.fields.get('transaction_direction').label = 'Rodzaj transakcji'
        form.fields.get('description').label = 'Opis'

        formset = SubTransactionFormSet(instance=transaction)
        formset.form.base_fields.get('amount').label = 'Kwota składowa (w groszach)'
        formset.form.base_fields.get('description').label = 'Opis'

    return render(request, 'account/transaction_form.html', {
        'form': form,
        'formset': formset,
        'accounts': all_accounts,
    })

def transaction_list(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    transactions = Transaction.objects.all().order_by('-date')
    return render(request, 'account/transactions_list.html', {
        'transactions': transactions,
        'accounts': all_accounts,
    })