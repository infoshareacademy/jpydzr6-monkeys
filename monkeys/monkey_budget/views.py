from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import MoneyAccount, Transaction, SubTransaction
from django.template.loader import render_to_string
from django.contrib import messages
from .forms import *
from .money import currencies
from .tests.test_currency_helper import all_currencies


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
            'balance': Monetary(chosen_account.balance, chosen_account.currency).amount_as_decimal
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
        if form.is_valid():
            formset = SubTransactionFormSet(request.POST)
            formset.instance = form.instance
            if formset.is_valid():
                with transaction.atomic():
                    transaction_form = form.save()
                    formset.instance = transaction_form
                    formset.save()
                    return redirect('lista-transakcji')
            else:
                for error in formset.non_form_errors():
                    messages.error(request, error)
    else:
        form = TransactionForm()
        formset = SubTransactionFormSet()
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    context = {
        'header': header,
        'form': form,
        'formset': formset,
        'accounts': all_accounts,
    }
    return render(request, 'account/transaction_form.html', context)


def transaction_update_view(request, transaction_id):
    header = 'Edycja transakcji'
    obj = get_object_or_404(Transaction, id=transaction_id)
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=obj)
        formset = SubTransactionFormSet(request.POST, instance=obj)
        formset.extra = 0
        context = {
            'header': header,
            'form': form,
            'formset': formset,
            'accounts': all_accounts,
        }
        if all([form.is_valid(), formset.is_valid()]):
            with transaction.atomic():
                transaction_form = form.save()
                formset.instance = transaction_form
                formset.save()
            messages.success(request, 'Edycja transakcji udana!')
            return redirect('edytuj-transakcje', transaction_id)
        else:
            for error in formset.non_form_errors():
                messages.error(request, error)
    else:
        form = TransactionForm(instance=obj)
        formset = SubTransactionFormSet(instance=obj)
        formset.extra = 0
        context = {
            'header': header,
            'form': form,
            'formset': formset,
            'accounts': all_accounts,
        }
    return render(request, 'account/transaction_form.html', context)


def transaction_list(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    transactions = Transaction.objects.all()
    return render(request, 'account/transactions_list.html', {
        'transactions': transactions,
        'accounts': all_accounts,
    })

def general_financial_report(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    all_transactions = Transaction.objects.all()
    all_currencies_balance = []
    account_balances = []

    # if request.method == 'POST':
    #     form = MonthlyFinancialReport(request.POST)
    #     if form.is_valid():
    #         month = form.cleaned_data['month']
    #         year = form.cleaned_data['year']
    # else:
    #     form = MonthlyFinancialReport()

    for currency in currencies.__all__:
        chosen_accounts = all_accounts.filter(currency_code=currency)
        currency_balance = 0
        for account in chosen_accounts:
            currency_balance += account.balance
        decimal_currency_balance = Monetary(currency_balance, CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal
        all_currencies_balance.append((currency,decimal_currency_balance))

    for account_type in MoneyAccount.types:
        type_code = account_type[0]
        type_name = account_type[1].capitalize()
        type_data = {
            'type_name': type_name,
            'currency_balances': []
        }

        for currency in currencies.__all__:
            accounts = all_accounts.filter(type=type_code, currency_code=currency)
            total_balance = sum(account.balance for account in accounts)
            type_data['currency_balances'].append((
                    Monetary(total_balance, CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal,
                    currency
                ))

        account_balances.append(type_data)

    context = {
        'accounts': all_accounts,
        'transactions': all_transactions,
        'all_currencies_balance': all_currencies_balance,
        'account_balances': account_balances,
    }
    return render(request, 'account/general_financial_report.html', context)

def periodic_financial_report(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')

    context = {
        'accounts': all_accounts,
    }
    return render(request, 'account/periodic_financial_report.html', context)

def filter_financial_reports(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    transactions = Transaction.objects.all()
    user_balance = 0
    report_data = []
    if request.method == 'POST':
        form = FinancialReport(request.POST)
        if form.is_valid():
            selected_accounts = form.cleaned_data.get('account_name')

            if selected_accounts:
                report_data = [
                    {
                        'name': account.name,
                        'balance': account.balance,
                        'currency': account.currency_code
                    }
                    for account in selected_accounts
                ]
        else:
            form = FinancialReport()

    form = FinancialReport()

    context = {'accounts': all_accounts,
               'transactions': transactions,
               'user_balance': user_balance,
               'form': form,
               'report_data': report_data,}
    return render(request, 'account/financial_reports.html', context)
