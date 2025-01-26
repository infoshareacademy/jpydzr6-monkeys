import pytest
from django.apps import apps
from django.db import models


@pytest.mark.django_db
def test_money_account_name_data_type():
    MoneyAccount = apps.get_model('monkey_budget', 'MoneyAccount')
    name = MoneyAccount._meta.get_field('name')
    assert isinstance(name, models.CharField)

@pytest.mark.django_db
def test_money_account_balance_data_type():
    MoneyAccount = apps.get_model('monkey_budget', 'MoneyAccount')
    balance = MoneyAccount._meta.get_field('balance')
    assert isinstance(balance, models.BigIntegerField)

@pytest.mark.django_db
def test_money_account_type_data_type():
    MoneyAccount = apps.get_model('monkey_budget', 'MoneyAccount')
    type = MoneyAccount._meta.get_field('type')
    assert isinstance(type, models.CharField)

@pytest.mark.django_db
def test_money_account_currency_code_data_type():
    MoneyAccount = apps.get_model('monkey_budget', 'MoneyAccount')
    currency_code = MoneyAccount._meta.get_field('currency_code')
    assert isinstance(currency_code, models.CharField)

@pytest.mark.django_db
def test_money_account_description_data_type():
    MoneyAccount = apps.get_model('monkey_budget', 'MoneyAccount')
    description = MoneyAccount._meta.get_field('description')
    assert isinstance(description, models.TextField)

@pytest.mark.django_db
def test_money_account_number_data_type():
    MoneyAccount = apps.get_model('monkey_budget', 'MoneyAccount')
    number = MoneyAccount._meta.get_field('number')
    assert isinstance(number, models.CharField)
