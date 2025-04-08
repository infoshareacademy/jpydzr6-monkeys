from decimal import Decimal

from django.contrib.auth.models import User
from django.views.generic import CreateView, UpdateView
from django.db import transaction as db_transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from django.utils.formats import number_format
from django.urls import reverse_lazy
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
        step = f"0.{'0' * (currency['exponent'] - 1)}1" if currency['exponent'] > 0 else "1"
        placeholder = f"0.{'0' * (currency['exponent'])}" if currency['exponent'] > 0 else "0"
        placeholder = Decimal(placeholder)
        placeholder = number_format(placeholder, decimal_pos=currency['exponent'])
        return Response({
            'step': step,
            'placeholder': placeholder,
        })
    except MoneyAccount.DoesNotExist:
        raise NotFound(detail='Money account not found')


class TransactionFormMixin:
    model = Transaction
    form_class = TransactionForm
    template_name = 'transaction/transaction_form.html'
    success_url = reverse_lazy('monkey_budget:lista-transakcji')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['header'] = self.get_header()

        form = context.get('form')

        if self.request.POST and form.is_valid():
            context['formset'] = SubTransactionFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={
                    'main_transaction_account': form.cleaned_data.get('account'),
                }
            )
        elif self.request.POST:
            context['formset'] = SubTransactionFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            # request.GET
            context['formset'] = SubTransactionFormSet(instance=self.object)

        context['accounts'] = MoneyAccount.objects.filter(user_id=self.request.user.id).order_by('name')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context.get('formset')

        if formset.is_valid():
            with db_transaction.atomic():
                self.object = form.save()
                formset.instance = self.object
                formset.save()
                return redirect(self.success_url)
        else:
            for error in formset.errors:
                messages.error(self.request, error)
            return self.form_invalid(form)


class TransactionCreateView(TransactionFormMixin, CreateView):
    def get_header(self):
        return 'Nowa transakcja'


class TransactionUpdateView(TransactionFormMixin, UpdateView):
    def get_header(self):
        return 'Edytuj transakcję'


def transaction_list(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    transactions = Transaction.objects.all()
    return render(request, 'transaction/transactions_list.html', {
        'transactions': transactions,
        'accounts': all_accounts,
    })
