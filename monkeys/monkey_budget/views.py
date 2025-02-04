from django.http import HttpResponse
from django.shortcuts import render

from .models import MoneyAccount


# Create your views here.

def money_accounts(request):
    context = {'accounts': MoneyAccount.objects.all()}
    return render(request, 'account_menu.html', context)

def add_money_account(request):
    return render(request, 'add_account.html')

def edit_money_account(request):
    return render(request, 'edit_account.html')

def delete_money_account(request):
    return render(request, 'delete_account.html')

def show_money_account(request, account_id):
    # context = {'accounts': MoneyAccount.objects.all()}
    # return render(request, 'show_account.html', context)
    return HttpResponse(f'Szczegóły konta numer: {account_id}')
