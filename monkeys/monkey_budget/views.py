from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def money_accounts(request):
    return HttpResponse("Zarządzanie zasobami pieniężnymi.")
