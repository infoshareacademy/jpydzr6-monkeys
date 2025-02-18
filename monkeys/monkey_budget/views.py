from django.shortcuts import render, get_object_or_404

from .models import MoneyAccount


# Create your views here.
# TODO - brak informacji o id użytkownika, jest wpisane na sztywno do zmiany po dodaniu możliwości logowania
def money_accounts(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    context = {'accounts': all_accounts}
    return render(request, 'account/account_menu.html', context)

def show_money_account(request, account_id):
    chosen_account = get_object_or_404(MoneyAccount, pk=account_id)
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    context = {'account': chosen_account, 'accounts': all_accounts}
    return render(request, 'account/show_account.html', context)

def add_money_account(request):
    return render(request, 'account/add_account.html')

def edit_money_account(request):
    return render(request, 'account/edit_account.html')

def delete_money_account(request):
    return render(request, 'account/delete_account.html')
