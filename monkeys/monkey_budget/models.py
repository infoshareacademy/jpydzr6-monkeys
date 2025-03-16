import decimal
from decimal import Decimal
from django.core.validators import ValidationError, MinValueValidator
from django.db import models, transaction
from django.contrib.auth.models import User
import django.utils.timezone
from .money import Monetary, CurrencyHelper, Currency


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
    possibly_negative = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name}: {self.balance_formatted}'

    @property
    def currency(self) -> Currency:
        return CurrencyHelper.get_currency_by_its_code(self.currency_code)

    @property
    def balance_formatted(self) -> Monetary:
        return Monetary(self.balance, self.currency)

    def get_type_display_name(self):
        return dict(self.types).get(self.type, self.type)

    def modify_balance(self, new_balance: int) -> None:
        self.balance = new_balance
        self.save()

    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'Money Account'


class Transaction(models.Model):
    # TODO: Jeżeli konto miałoby zostać kiedyś usunięte to w przypadku, gdy posiada transakcje, być może powinno one
    #  zostać zarchiwizowane (dla raportów, w zależności jak będa one generowane lub dla zachowania faktur/paragonów
    #  związanych z gwarancją)
    account = models.ForeignKey(MoneyAccount, on_delete=models.deletion.CASCADE, related_name='transaction')
    date = models.DateTimeField(default=django.utils.timezone.now)
    total = models.BigIntegerField(
        validators=[MinValueValidator(
            limit_value=0,
            message='Transaction total value must be nonnegative')],
        default=0,
        editable=False)
    transaction_directions = [('IN', 'income'), ('OUT', 'outcome')]
    transaction_direction = models.CharField(choices=transaction_directions, max_length=3, default='OUT')
    balance_after_transaction = models.BigIntegerField(editable=False, default=0)
    description = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = 'monkey_budget'

    def __str__(self):
        money = Monetary(int(self.total), self.currency)
        return f"{self.transaction_direction} transaction of total {money}"

    @property
    def currency(self):
        return self.account.currency

    @property
    def total_formatted(self) -> Monetary:
        return Monetary(self.total, self.currency)

    @property
    def balance_after_transaction_formatted(self) -> Monetary:
        return Monetary(self.balance_after_transaction, self.currency)

class SubTransaction(models.Model):
    main_transaction = models.ForeignKey(Transaction, on_delete=models.deletion.CASCADE,
                                         related_name='sub_transaction')
    amount = models.BigIntegerField(validators=[MinValueValidator(limit_value=0, message='Transaction total value must be nonnegative')])
    description = models.CharField(max_length=100, blank=True)

    def __str__(self):
        money = Monetary(int(self.amount), CurrencyHelper.get_currency_by_its_code(self.main_transaction.account.currency_code))
        return f"Transaction component ({money})"

    @property
    def currency(self):
        return self.main_transaction.currency

    @property
    def amount_formatted(self) -> Monetary:
        return Monetary(self.amount, self.currency)
