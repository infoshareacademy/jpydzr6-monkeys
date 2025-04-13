from decimal import Decimal

from django.contrib.auth.models import User
from django.views.generic import CreateView, UpdateView, DetailView, ListView, DeleteView
from django import forms
from django.db import transaction as db_transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from django.utils.formats import number_format
from django.utils import timezone
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, FileResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from ..models import MoneyAccount, Transaction, TransactionAttachment
from ..forms import *
from django.views import View


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_account_currency_info(request, account_id):
    try:
        account = MoneyAccount.objects.get(pk=account_id)
        if account.user_id != request.user:
            # Zabezpieczenie przed odpytywaniem api bez zalogowanego użytkownika
            raise PermissionDenied(detail="You must be logged in to request this data")
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
                return HttpResponseRedirect(self.get_success_url())
        else:
            if formset.errors:
                messages.error(self.request, "Sprawdź poprawność wprowadzonych danych")
            for error in formset.non_form_errors():
                messages.error(self.request, error)
            return self.form_invalid(form)


@method_decorator(login_required, name="dispatch")
class TransactionCreateView(TransactionFormMixin, CreateView):
    def get_header(self):
        return 'Nowa transakcja'

    def get_success_message(self):
        return f"Transakcja została dodana"

    def form_valid(self, form):
        response = super().form_valid(form)
        async_attachment_ids = self.request.POST.get('async_attachment_ids')
        if async_attachment_ids:
            ids = [int(i) for i in async_attachment_ids.split(',') if i.strip().isdigit()]
            TransactionAttachment.objects.filter(pk__in=ids, transaction__isnull=True).update(transaction=self.object)
        return redirect('monkey_budget:transaction-update', pk=self.object.pk)

@method_decorator(login_required, name="dispatch")
class TransactionUpdateView(TransactionFormMixin, UpdateView):
    def get_header(self):
        return 'Edytuj transakcję'

    def get_success_message(self):
        return f"Transakcja została pomyślnie edytowana"

    def get_success_url(self):
        url = reverse_lazy('monkey_budget:transaction-detail', kwargs={'pk': self.object.pk})
        return url


@method_decorator(login_required, name="dispatch")
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


@method_decorator(login_required, name="dispatch")
class TransactionDeleteView(DeleteView):
    model = Transaction
    template_name = 'transaction/transaction_delete.html'
    success_url = reverse_lazy('monkey_budget:transaction-list')

    def form_valid(self, form):
        messages.success(self.request, "Transakcja została usunieta")
        return super().form_valid(form)


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
        context['header'] = 'Lista transakcji'
        if not self.request.GET:
            initial_filter_form = {
                'date_to': timezone.localdate().strftime('%Y-%m-%d'),
            }
            context['filter_form'] = TransactionFilterForm(initial=initial_filter_form)
        else:
            context['filter_form'] = TransactionFilterForm(self.request.GET)

        transactions = self.object_list
        for transaction in transactions:
            transaction_direction = transaction.transaction_direction
            transaction.transaction_direction_display = "Przychód" if transaction_direction == 'IN' else "Wydatek"
        context['transactions'] = transactions
        return context


@method_decorator(login_required, name="dispatch")
class TransactionListView(TransactionListMixin, ListView):
    template_name = 'transaction/transactions_list.html'

    def get_queryset(self):
        return self.get_base_queryset()


@method_decorator(login_required, name="dispatch")
class AccountTransactionListView(TransactionListMixin, ListView):
    template_name = 'transaction/account_transactions_list.html'
    default_sort_field = 'id'
    default_sort_order = 'asc'

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        sort_by = self.kwargs.get('sort_by', self.default_sort_field)
        order = self.kwargs.get('order', self.default_sort_order)
        allowed_fields = [f.name for f in self.model._meta.get_fields()]
        if sort_by not in allowed_fields:
            sort_by = self.default_sort_field

        if order.lower() == 'desc':
            sort_by = '-' + sort_by
        return self.get_base_queryset().filter(account_id=account_id).order_by(sort_by)

@method_decorator(login_required, name='dispatch')
class AttachmentMixin(View):
    def get_transaction(self, transaction_id):
        return get_object_or_404(Transaction, pk=transaction_id)

@method_decorator(login_required, name='dispatch')
class AttachmentAddView(AttachmentMixin):
    def post(self, request, transaction_id):
        try:
            transaction = self.get_transaction(transaction_id)
            form = TransactionAttachmentForm(request.POST, request.FILES)
            if form.is_valid():
                attachment = form.save(commit=False)
                attachment.transaction = transaction
                attachment.save()
                messages.success(request, "Załącznik został dodany.")
                return redirect('monkey_budget:transaction-detail', pk=transaction_id)
            else:
                messages.error(request, "Błąd w formularzu: " + str(form.errors))
                return redirect('monkey_budget:transaction-detail', pk=transaction_id)
        except Exception as e:
            messages.error(request, f"Błąd przy dodawaniu załącznika: {e}")
            return redirect('monkey_budget:transaction-detail', pk=transaction_id)
    def get(self, request, transaction_id):
        return HttpResponse(status=405)

@method_decorator(login_required, name='dispatch')
class AttachmentDeleteView(AttachmentMixin):
    def post(self, request, pk):
        try:
            attachment = get_object_or_404(TransactionAttachment, pk=pk)
            transaction_id = attachment.transaction.pk
            attachment.delete()
            messages.success(request, "Załącznik został usunięty.")
            return redirect('monkey_budget:transaction-detail', pk=transaction_id)
        except Exception as e:
            messages.error(request, f"Błąd przy usuwaniu załącznika: {e}")
            try:
                transaction_id = attachment.transaction.pk
            except Exception:
                transaction_id = ''
            return redirect('monkey_budget:transaction-detail', pk=transaction_id)

@method_decorator(login_required, name='dispatch')
class AttachmentDownloadView(AttachmentMixin):
    def get(self, request, pk):
        try:
            attachment = get_object_or_404(TransactionAttachment, pk=pk)
            return FileResponse(attachment.file.open('rb'), as_attachment=True)
        except Exception as e:
            messages.error(request, f"Błąd przy pobieraniu załącznika: {e}")
            try:
                transaction_id = attachment.transaction.pk
            except Exception:
                transaction_id = ''
            return redirect('monkey_budget:transaction-detail', pk=transaction_id)

@method_decorator(login_required, name='dispatch')
class AttachmentUploadView(View):
    def post(self, request):
        form = TransactionAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.transaction = None
            attachment.save()
            return JsonResponse({'success': True, 'attachment_id': attachment.pk})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)