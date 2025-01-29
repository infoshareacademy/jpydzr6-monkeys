from django.http import HttpResponse


# Create your views here.

def money_accounts(request):
    return HttpResponse('Subemnu zarządzania kontami.')

def add_money_account(request):
    return HttpResponse('Dodawanie konta')

def edit_money_account(request):
    return HttpResponse('Edycja konta')

def delete_money_account(request):
    return HttpResponse('Usuwanie konta')

def show_money_account(request):
    return HttpResponse('Pokaż konta')
