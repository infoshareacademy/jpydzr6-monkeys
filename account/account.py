from decimal import Decimal

from peewee import *

db = SqliteDatabase('budget.db')

#model stworzony do testów
class User(Model):
    DoesNotExist = None
    user_id = AutoField()
    class Meta:
        database = db

class Currency(Model):
    DoesNotExist = None
    currency_id = AutoField()
    currency_name = CharField()
    class Meta:
        database = db

class Account(Model):
    DoesNotExist = None
    account_id = AutoField()
    account_number = IntegerField(unique=True)
    account_name = CharField()
    balance = DecimalField(decimal_places=2)
    user_id = ForeignKeyField(User)
    currency_id = ForeignKeyField(Currency)

    class Meta:
        database = db

db.connect()
db.create_tables([Account])

class AccountManager:

    def add_account(
                    self,
                    account_number: int,
                    account_name: str,
                    balance: Decimal,
                    user_id: int,
                    currency_id: int
    ) -> None:

        account = Account.create(
                          account_number=account_number,
                          account_name=account_name,
                          balance=balance,
                          user_id=user_id,
                          currency_id=currency_id
        )

        print(f'Konto o numerze {account_number} zostało utworzone.')
#todo walidacja danych - sprawdzenie typu, wartości, czy user_id istnieje,
# zapytaj do jakiego użytkownika przypisać konto 