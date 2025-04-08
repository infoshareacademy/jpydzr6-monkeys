from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, Value
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.functions import Coalesce
from .models import MoneyAccount, Transaction, SubTransaction
from django.template.loader import render_to_string
from django.contrib import messages
from .forms import *
from .money import currencies


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
    transactions = Transaction.objects.filter(account__user_id=2)
    return render(request, 'account/transactions_list.html', {
        'transactions': transactions,
        'accounts': all_accounts,
    })


def periodic_financial_report(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    start_date = (date.today() - timedelta(days=30))
    end_date = (date.today())
    currency_incomes_outcomes_balance = {'balances':[]}
    date_filtered_transactions = None

    if request.method == 'POST':
        form = PeriodicFinancialReport(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            extended_end_date = end_date + timedelta(days=1)
            date_filtered_transactions = Transaction.objects.filter(
                account__user_id=2,
                date__range=(start_date, extended_end_date)
            )

            # todo wyświatelanie jako tabela
            # todo nie można brać aktualnego balansu konta - jest brany też dla okresów kiedy konto nie istniało,
            #  lepiej brać saldo z ostatniej transakcji na danym koncie
            # todo obsłuż sytuację, że dla danego okresu nie ma danych do wyświetlenia
            for currency in currencies.__all__:
                currency_balance_after_period = []
                all_accounts_currency_filtered = all_accounts.filter(currency_code=currency)
                if all_accounts_currency_filtered:
                    for account in all_accounts.filter(currency_code=currency):
                        ordered_transactions = date_filtered_transactions.filter(account_id=account.id).order_by('-date')
                        if ordered_transactions:
                            end_period_account_balance = ordered_transactions[0].balance_after_transaction
                        else:
                            end_period_account_balance = account.balance
                        currency_balance_after_period.append(end_period_account_balance)
                    balance_after_period = sum(currency_balance_after_period)

                    incomes_total = date_filtered_transactions.filter(
                        account__currency_code= currency,
                        transaction_direction='IN'
                    ).aggregate(total_sum=Coalesce(Sum('total'), Value(0)))

                    outcomes_total = date_filtered_transactions.filter(
                        account__currency_code= currency,
                        transaction_direction='OUT'
                    ).aggregate(total_sum=Coalesce(Sum('total'), Value(0)))
                    income_outcome_balance = incomes_total['total_sum'] - outcomes_total['total_sum']

                    currency_incomes_outcomes_balance['balances'].append({
                            'currency_code': currency,
                            'incomes_total': incomes_total,
                            'outcomes_total': outcomes_total,
                            'income_outcome_balance': income_outcome_balance,
                            'balance_after_period': balance_after_period,
                        })
    else:
        form = PeriodicFinancialReport()

    context = {
        'accounts': all_accounts,
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'currency_incomes_outcomes_balance': currency_incomes_outcomes_balance,
        'date_filtered_transactions': date_filtered_transactions,
    }
    return render(request, 'account/periodic_financial_report.html', context)
