from django.db import models
from django.db.models import BigIntegerField
from django.contrib.auth.models import User


# Create your models here.


class MoneyAccount(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    user_id = models.ForeignKey(User, related_name='money_accounts', on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100) # krótka nazwa konta nadawana przez użytkownika np. 'Oszczędnościowe mbank'
    balance = BigIntegerField()
    types = ['konto bankowe', 'gotówka', 'bony', 'inne'] # typy przechowywania pieniędzy do wybrania przez użytkownika
    type = models.CharField(choices=types, max_length=50, default='konto bankowe') # typ konta do wybrania z pośród podanych kategorii
    currency_code = ['PLN', 'USD', 'EUR']
    currency_code = models.CharField(choices=currency_code, max_length=3, default='PLN') #ISO4217 np. PLN, USD
    description = models.TextField(max_length=512) # dłuższy opis konta dodawany przez użytkownika
    number = models.CharField(max_length=50, default=None, null=True) # numer konta dodawany przez użytkownika,
                                                                    # w zamyśle pełen numer konta bankowego lub
                                                                    # brak np. dla gotówki czy bonów
    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'Money Account'
