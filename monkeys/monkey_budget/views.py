from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import MoneyAccount, Transaction, SubTransaction
from django.template.loader import render_to_string
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from django.utils.formats import number_format
from .forms import *


# TODO - brak informacji o id użytkownika, jest wpisane na sztywno do zmiany po dodaniu możliwości logowania

def home(request):
    return render(request, 'home.html')

def team(request):
    return render(request, 'team.html')

def contact(request):
    return render (request, 'contact.html')

def dashboard(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    context = {'accounts': all_accounts}
    return render(request, 'account/dashboard.html', context)

def show_accounts_list(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    context = {'accounts': all_accounts}
    return render(request, 'account/show_accounts_list.html', context)

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
            return redirect(f'/konta/{chosen_account.id}')
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

@api_view(['GET'])
# TODO: Kiedy użytkownik zostanie zaimplementowany, odkomentować linię z @permission classes. Niewykluczone, że będzie
#  potrzebny też dopuszczenie metody autentykacji przez sesję, wtedy nalezy dodać @authentication_classes([SessionAuthentication
#  Ponadto odkomentować blok warunkowy `if account.user_id != request.user:`
@permission_classes([IsAuthenticated])
def get_account_currency_info(request, account_id):
    try:
        account = MoneyAccount.objects.get(pk=account_id)
        # if account.user_id != request.user:
        #     # Zabezpieczenie przed odpytywaniem api bez zalogowanego użytkownika
        #     raise PermissionDenied(detail="You must be logged in to request this data")
        currency = account.currency
        step = f"0.{'0' * (currency['exponent']-1)}1" if currency['exponent'] > 0 else "1"
        placeholder = f"0.{'0' * (currency['exponent'])}" if currency['exponent'] > 0 else "0"
        placeholder = Decimal(placeholder)
        placeholder = number_format(placeholder, decimal_pos=currency['exponent'])
        return Response({
            'step': step,
            'placeholder': placeholder,
        })
    except MoneyAccount.DoesNotExist:
        raise NotFound(detail='Money account not found')


def transaction_create_view(request):
    header = 'Nowa transakcja'
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            formset = SubTransactionFormSet(
                request.POST,
                form_kwargs={
                    'main_transaction_account': form.cleaned_data.get('account'),
                }
            )
            if formset.is_valid():
                with transaction.atomic():
                    transaction_form = form.save()
                    formset.instance = transaction_form
                    formset.save()
                    return redirect('monkey_budget:lista-transakcji')
            else:
                for error in formset.non_form_errors():
                    messages.error(request, error)
        else:
            formset = SubTransactionFormSet(request.POST)
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
            return redirect('monkey_budget:edytuj-transakcje', transaction_id)
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