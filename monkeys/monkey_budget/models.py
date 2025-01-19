from django.db import models
from django.db.models import BigIntegerField


# Create your models here.


class MoneyAccount(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    name = models.CharField(max_length=100) # krótka nazwa konta nadawana przez użytkownika np. 'Oszczędnościowe mbank'
    balance = BigIntegerField()
    currency_id = models.CharField(max_length=3) #ISO4217 np. PLN, USD
    description = models.CharField(max_length=512) # dłuższy opis konta dodawany przez użytkownika
    number = models.CharField(max_length=50, default=None, null=True) # numer konta dodawany przez użytkownika,
                                                                    # w zamyśle pełen numer konta bankowego lub
                                                                    # brak np. dla gotówki czy bonów

    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'Money Account'
