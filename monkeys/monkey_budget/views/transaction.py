from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from django.utils.formats import number_format
from ..models import MoneyAccount, Transaction, SubTransaction
from ..forms import *

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