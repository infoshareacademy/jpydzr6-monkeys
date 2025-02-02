from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.

def money_accounts(request):
    return HttpResponse('Subemnu zarządzania kontami.')

def add_money_account(request):
    return render(request, 'add_account.html')

def edit_money_account(request):
    return render(request, 'edit_account.html')

def delete_money_account(request):
    return render(request, 'delete_account.html')

def show_money_account(request):
    return render(request, 'add_account.html')
