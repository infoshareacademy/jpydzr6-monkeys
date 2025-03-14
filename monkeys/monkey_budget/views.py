from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import MoneyAccount, Transaction, SubTransaction
from django.template.loader import render_to_string
from .forms import *


# TODO - brak informacji o id użytkownika, jest wpisane na sztywno do zmiany po dodaniu możliwości logowania
def dashboard(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    context = {'accounts': all_accounts}
    return render(request, 'account/base.html', context)

def show_money_account(request, account_id):
    account_related_transactions = Transaction.objects.filter(account_id=account_id).order_by('-date')
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
            'balance': Monetary(chosen_account.balance, chosen_account.currency).decimal
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

def transaction_create_view(request):
    header = 'Nowa transakcja'
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        formset = SubTransactionFormSet(request.POST)
        if all([form.is_valid(), formset.is_valid()]):
            formset.save()
            redirect('lista-transakcji')
    else:
        form = TransactionForm()
        formset = SubTransactionFormSet()
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    context = {
        'header': header,
        'form': form,
        'formset': formset,
        'all_accounts': all_accounts,
    }
    return render(request, 'account/transaction_form.html', context)


def transaction_update_view(request, transaction_id):
    header = 'Edycja transakcji'
    obj = get_object_or_404(Transaction, id=transaction_id)
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=obj)
        formset = SubTransactionFormSet(request.POST, instance=obj)
        formset.extra = 0
        context = {
            'header': header,
            'form': form,
            'formset': formset,
            'all_accounts': all_accounts,
        }
        if form.is_valid() and formset.is_valid():
            formset.save()
            return redirect('edytuj-transakcje', transaction_id)
    else:
        form = TransactionForm(instance=obj)
        formset = SubTransactionFormSet(instance=obj)
        formset.extra = 0
        context = {
            'header': header,
            'form': form,
            'formset': formset,
            'all_accounts': all_accounts,
        }
    return render(request, 'account/transaction_form.html', context)


def transaction_list(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    transactions = Transaction.objects.all()
    return render(request, 'account/transactions_list.html', {
        'transactions': transactions,
        'accounts': all_accounts,
    })