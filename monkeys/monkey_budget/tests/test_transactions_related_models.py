import pytest
import django.utils.timezone
from django.core.exceptions import ValidationError

from ..models import MoneyAccount, Transaction, SubTransaction
from ..views.account import add_money_account

datetime_for_test = django.utils.timezone.now()


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(username='test', password='test')


@pytest.fixture
def money_account(db, user) -> MoneyAccount:
    return MoneyAccount.objects.create(
        id=1,
        user_id=user,
        name='test_account',
        balance=0,
        type='BA',
        currency_code='PLN',
        description='Account for testing purposes'
    )


@pytest.mark.django_db
def test_transaction_limit(money_account):
    with pytest.raises(ValidationError):
        transaction = Transaction(
            account=money_account,
            date=datetime_for_test,
            total=-1,
            transaction_direction='IN',
            balance_after_transaction=money_account.balance,
            description='No description'
        )
        # poniższe należy wywołać, żeby walidacja została przeprowadzona
        transaction.full_clean()


@pytest.mark.django_db
def test_sub_transaction_limit(money_account):
    transaction = Transaction(
        account=money_account,
        date=datetime_for_test,
        total=0,
        transaction_direction='IN',
        balance_after_transaction=money_account.balance,
        description='No description'
    )
    with pytest.raises(ValidationError):
        subtransaction = SubTransaction(
            main_transaction=transaction,
            amount=-1,
            description=''
        )
        subtransaction.full_clean()
