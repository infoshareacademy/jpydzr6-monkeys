from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import BigIntegerField
from django.contrib.auth.models import User
import django.utils.timezone

from .money import Monetary, CurrencyHelper


class MoneyAccount(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    user_id = models.ForeignKey(User, related_name='money_accounts', on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100) # krótka nazwa konta nadawana przez użytkownika np. 'Oszczędnościowe mbank'
    balance = BigIntegerField()
    types = [('BA', 'konto bankowe'), ('CA', 'gotówka'), ('CO', 'bony'), ('AN', 'inne')] # typy przechowywania pieniędzy do wybrania przez użytkownika
    type = models.CharField(choices=types, max_length=50, default='konto bankowe') # typ konta do wybrania z pośród podanych kategorii
    currency_code = models.CharField(choices=CurrencyHelper.get_currencies_set(), max_length=3, default='PLN') #ISO4217 np. PLN, USD
    description = models.TextField(max_length=512) # dłuższy opis konta dodawany przez użytkownika

    def __str__(self):
        return f'{self.name}: {self.balance} {self.currency_code}'


    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'Money Account'


class Transaction(models.Model):
    # TODO: Jeżeli konto miałoby zostać kiedyś usunięte to w przypadku, gdy posiada transakcje, być może powinno one
    #  zostać zarchiwizowane (dla raportów, w zależności jak będa one generowane lub dla zachowania faktur/paragonów
    #  związanych z gwarancją)
    account = models.ForeignKey(MoneyAccount, on_delete=models.deletion.CASCADE, related_name='transaction')
    date = models.DateTimeField(default=django.utils.timezone.now())
    total = models.BigIntegerField()
    transaction_directions = [('IN', 'income'), ('OUT', 'outcome')]
    transaction_direction = models.CharField(choices=transaction_directions, max_length=3, default='OUT')
    balance_after_transaction = models.BigIntegerField()
    description = models.CharField(max_length=100, default='')

class SubTransaction(models.Model):
    main_transaction = models.ForeignKey(Transaction, on_delete=models.deletion.CASCADE,
                                         related_name='sub_transaction')
    amount = models.BigIntegerField(validators=[MinValueValidator(limit_value=0, message='Transaction total value must be nonnegative')])
    description = models.CharField(max_length=100, blank=True)

