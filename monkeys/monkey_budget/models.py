from django.db import models
from django.db.models import BigIntegerField
from django.contrib.auth.models import User
from .money import CurrencyHelper


# Create your models here.


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


class MainCategory(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    user_id = models.ForeignKey(User, related_name='main_categories', on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100)
    category_types = [
        ('INC', 'Przychód'),
        ('EXP', 'Wydatek'),
    ]
    category_type = models.CharField(choices=category_types, max_length=3)
    description = models.TextField(max_length=512, blank=True)

    def __str__(self):
        return f'{self.name} ({self.get_category_type_display()})'

    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'Main Category'
        verbose_name_plural = 'Main Categories'


class SubCategory(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    parent_category = models.ForeignKey(MainCategory, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=512, blank=True)

    def __str__(self):
        return f'{self.parent_category.name} - {self.name}'

    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'Sub Category'
        verbose_name_plural = 'Sub Categories'
