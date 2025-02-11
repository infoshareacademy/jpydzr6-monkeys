from django.db import models
from django.contrib.auth.models import User
from .money import CurrencyHelper


# Create your models here.


class MoneyAccount(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    user_id = models.ForeignKey(User, related_name='money_accounts', on_delete=models.CASCADE, null=False)
    # krótka nazwa konta nadawana przez użytkownika np. 'Oszczędnościowe mbank'
    name = models.CharField(max_length=100)
    balance = models.BigIntegerField()
    #  typy przechowywania pieniędzy do wybrania przez użytkownika
    types = [('BA', 'konto bankowe'), ('CA', 'gotówka'), ('CO', 'bony'), ('AN', 'inne')]
    # typ konta do wybrania spośród podanych kategorii
    type = models.CharField(choices=types, max_length=50, default='konto bankowe')
    # ISO4217 np. PLN, USD
    currency_code = models.CharField(choices=CurrencyHelper.get_currencies_set(), max_length=3, default='PLN')
    # dłuższy opis konta dodawany przez użytkownika
    description = models.TextField(max_length=512)

    def __str__(self):
        return f'{self.name}: {self.balance} {self.currency_code}'

    def get_type_display_name(self):
        return dict(self.types).get(self.type, self.type)


    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'Money Account'
