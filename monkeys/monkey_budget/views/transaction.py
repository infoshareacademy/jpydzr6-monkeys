from decimal import Decimal

from django.contrib.auth.models import User
from django.views.generic import CreateView, UpdateView, DetailView, ListView, DeleteView
from django import forms
from django.db import transaction as db_transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from django.utils.formats import number_format
from django.utils import timezone
from django.urls import reverse_lazy
from ..models import MoneyAccount, Transaction
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
    success_url = reverse_lazy('monkey_budget:transaction-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

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
                messages.success(self.request, self.get_success_message())
                return redirect(self.get_success_url())
        else:
            if formset.errors:
                messages.error(self.request, "Sprawdź poprawność wprowadzonych danych")
            for error in formset.non_form_errors():
                messages.error(self.request, error)
            return self.form_invalid(form)


class TransactionCreateView(TransactionFormMixin, CreateView):
    def get_header(self):
        return 'Nowa transakcja'

    def get_success_message(self):
        return f"Transakcja została dodana"


class TransactionUpdateView(TransactionFormMixin, UpdateView):
    def get_header(self):
        return 'Edytuj transakcję'

    def get_success_message(self):
        return f"Transakcja została pomyślnie edytowana"

    def get_success_url(self):
        url = reverse_lazy('monkey_budget:transaction-detail', kwargs={'pk': self.object.pk})
        return url


class TransactionDetailView(DetailView):
    model = Transaction
    template_name = 'transaction/transaction_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction = self.object
        transaction_direction = transaction.transaction_direction
        context['transaction_direction'] = "Przychód" if transaction_direction == 'IN' else "Wydatek"

        context['subtransactions'] = transaction.subtransactions.all()

        return context


class TransactionDeleteView(DeleteView):
    pass


class TransactionFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        label="Data od",
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        label="Data do",
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', 'Data początkowa nie może być wcześniejsza niż końcowa')


class TransactionListMixin:
    model = Transaction
    paginate_by = 10
    context_object_name = "transactions"

    def get_base_queryset(self):
        queryset = Transaction.objects.filter(account__user_id=self.request.user).select_related('account').order_by('-id')
        filter_form = TransactionFilterForm(self.request.GET)

        if filter_form.is_valid():
            if filter_form.cleaned_data['date_from']:
                queryset = queryset.filter(date__gte=filter_form.cleaned_data['date_from'])
            if filter_form.cleaned_data['date_to']:
                queryset = queryset.filter(date__lte=filter_form.cleaned_data['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.GET:
            initial_filter_form = {
                'date_to': timezone.localdate().strftime('%Y-%m-%d'),
            }
            context['filter_form'] = TransactionFilterForm(initial=initial_filter_form)
        else:
            context['filter_form'] = TransactionFilterForm(self.request.GET)
        context['header'] = 'Lista transakcji'
        return context


class TransactionListView(TransactionListMixin, ListView):
    template_name = 'transaction/transactions_list.html'

    def get_queryset(self):
        return self.get_base_queryset()


class AccountTransactionListView(TransactionListMixin, ListView):
    template_name = 'transaction/account_transactions_list.html'

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        return self.get_base_queryset().filter(account_id=account_id)


def transaction_list(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    transactions = Transaction.objects.all()
    return render(request, 'transaction/transactions_list.html', {
        'transactions': transactions,
        'accounts': all_accounts,
    })
