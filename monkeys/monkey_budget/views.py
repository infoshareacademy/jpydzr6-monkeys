from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import MoneyAccount, Transaction, SubTransaction, TransactionAttachment
from django.template.loader import render_to_string
from django.contrib import messages
from .forms import *
from django.http import FileResponse


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
        sub_formset = SubTransactionFormSet(request.POST)
        attach_formset = TransactionAttachmentFormSet(request.POST, request.FILES)

        if all([
            form.is_valid(),
            sub_formset.is_valid(),
            attach_formset.is_valid()
        ]):
            with transaction.atomic():
                # Zapisz główną transakcję
                transaction_obj = form.save()

                # Zapisz subtransakcje
                sub_formset.instance = transaction_obj
                sub_formset.save()

                # Zapisz załączniki
                attach_formset.instance = transaction_obj
                attach_formset.save()

            return redirect('lista-transakcji')
    else:
        form = TransactionForm()
        sub_formset = SubTransactionFormSet()
        attach_formset = TransactionAttachmentFormSet()

    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    context = {
        'header': header,
        'form': form,
        'formset': sub_formset,
        'attach_formset': attach_formset,
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
    transactions = Transaction.objects.all()

    for t in transactions:
        image_attachments = []
        other_attachments = []
        for attach in t.attachments.all():
            name = attach.file.name.lower()
            if name.endswith(('.png', '.jpg', '.jpeg')):
                image_attachments.append(attach)
            else:
                other_attachments.append(attach)

        t.image_attachments = image_attachments
        t.other_attachments = other_attachments

    return render(request, 'account/transactions_list.html', {
        'transactions': transactions
    })

def attachment_add(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        form = TransactionAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.transaction = transaction # przypisanie do transakcji
            attachment.save()
            return redirect('lista-transakcji') #redirect
    else:
        form = TransactionAttachmentForm()
    return render(request, 'account/attachment_add.html', {
        'form': form,
        'transaction': transaction
    })

def attachment_download(request, pk):
    attachment = get_object_or_404(TransactionAttachment, pk=pk)
    return FileResponse(attachment.file.open('rb'), as_attachment=True)

def attachment_delete(request, pk):
    attachment = get_object_or_404(TransactionAttachment, pk=pk)
    transaction_pk = attachment.transaction.pk
    attachment.delete()
    return redirect('lista-transakcji')

