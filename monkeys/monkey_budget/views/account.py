from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.functions import Coalesce
from django.db.models import Sum, Value
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from .transaction import AccountTransactionListView
from ..models import MoneyAccount
from ..money import CurrencyHelper, currencies
from ..forms import *


@login_required
def show_accounts_list(request):
    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id).order_by('name')
    context = {'accounts': all_accounts}
    return render(request, 'account/show_accounts_list.html', context)

@login_required
def show_money_account(request, account_id):
    chosen_account = get_object_or_404(MoneyAccount, pk=account_id)
    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id).order_by('name')

    query_params = {
        'sort_by': 'date',
        'order': 'desc',
    }
    # account_related_transactions_view_instance = AccountTransactionListView()
    # account_related_transactions_view_instance.setup(request, **query_params)
    # try:
    #     account_related_transactions = account_related_transactions_view_instance.get_queryset()
    # except Exception as e:
    #     print(f"Error getting queryset from AccountTransactionListView: {e}")
    #     account_related_transactions = AccountTransactionListView.model.objects.none()
    account_related_transactions_view = AccountTransactionListView.as_view()
    response = account_related_transactions_view(request, account_id=account_id, **query_params)
    if hasattr(response, 'render') and callable(response.render):
        response.render()
    account_related_transactions = response.content.decode('utf-8')
    context = {'account': chosen_account,
               'accounts': all_accounts,
               'transactions_list_html': account_related_transactions}
    return render(request, 'account/show_account.html', context)

@login_required
def add_money_account(request):
    if request.method == 'POST':
        form = MoneyAccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user_id = request.user
            account.balance = Monetary.major_to_minor_unit(form.cleaned_data['balance'], account.currency)
            account.save()
            return redirect(f'/konta/{account.id}')
    else:
        form = MoneyAccountForm()
    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id).order_by('name')
    return render(request, 'account/add_account.html', {'form': form, 'accounts': all_accounts})

@login_required
def edit_money_account(request, account_id):
    chosen_account = get_object_or_404(MoneyAccount, pk=account_id, user_id=request.user.id)
    if request.method == 'POST':
        form = MoneyAccountForm(request.POST, instance=chosen_account)
        if form.is_valid():
            account = form.save(commit=False)
            account.balance = Monetary.major_to_minor_unit(form.cleaned_data['balance'], account.currency)
            form.save()
            return redirect(f'/konta/{chosen_account.id}')
    else:
        initial_data = {
            'balance': Monetary(chosen_account.balance, chosen_account.currency).amount_as_decimal
        }
        form = MoneyAccountForm(instance=chosen_account, initial=initial_data)

    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id).order_by('name')
    context = {'account': chosen_account, 'accounts': all_accounts, 'form': form}
    return render(request, 'account/edit_account.html', context)

@login_required
def delete_money_account(request, account_id):
    if request.method == 'POST':
        account = get_object_or_404(MoneyAccount, id=account_id, user_id=request.user.id)
        account.delete()
        return JsonResponse({'success': True, 'message': _('Konto zostało usunięte.')})
    return JsonResponse({'success': False, 'message': _('Invalid request.')})


@login_required
def general_financial_report(request):
    all_accounts = MoneyAccount.objects.filter(user_id=request.user).order_by('name')
    all_currencies_balance = []
    account_balances = []

    for currency in currencies.__all__:
        chosen_accounts = all_accounts.filter(currency_code=currency)
        currency_balance = sum(account.balance for account in chosen_accounts)
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
        'all_currencies_balance': all_currencies_balance,
        'account_balances': account_balances,
    }
    return render(request, 'account/general_financial_report.html', context)

@login_required
def periodic_financial_report(request):
    all_accounts = MoneyAccount.objects.filter(user_id=request.user).order_by('name')
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
                account__user_id=request.user,
                date__range=(start_date, extended_end_date)
            )

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
                            'incomes_total': Monetary(incomes_total['total_sum'], CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal,
                            'outcomes_total': Monetary(outcomes_total['total_sum'], CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal,
                            'income_outcome_balance': Monetary(income_outcome_balance, CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal,
                            'balance_after_period': Monetary(balance_after_period, CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal,
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

