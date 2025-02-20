from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from .models import MoneyAccount
from .forms import MoneyAccountForm


# Create your views here.
# TODO - brak informacji o id użytkownika, jest wpisane na sztywno do zmiany po dodaniu możliwości logowania
def dashboard(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    context = {'accounts': all_accounts}
    return render(request, 'account/base.html', context)

def show_money_account(request, account_id):
    chosen_account = get_object_or_404(MoneyAccount, pk=account_id)
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    context = {'account': chosen_account, 'accounts': all_accounts}
    return render(request, 'account/show_account.html', context)

def add_money_account(request):
    if request.method == 'POST':
        form = MoneyAccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user_id = User.objects.get(pk=2)
            account.save()
            return redirect('dashboard')
    else:
        form = MoneyAccountForm()
    all_accounts = MoneyAccount.objects.filter(user_id=2)
    return render(request, 'account/add_account.html', {'form': form, 'accounts': all_accounts})

def edit_money_account(request):
    return render(request, 'account/edit_account.html')

def delete_money_account(request, account_id):
    account = get_object_or_404(MoneyAccount, id=account_id)
    account.delete()
    return redirect('dashboard')
