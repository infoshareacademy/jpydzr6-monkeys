from decimal import Decimal

from peewee import *

db = SqliteDatabase('budget.db')


class Account(Model):
    DoesNotExist = None
    account_id = AutoField()
    account_number = IntegerField(unique=True)
    account_name = CharField()
    balance = DecimalField(decimal_places=2)
    user_id = IntegerField()
    currency = CharField()

    class Meta:
        database = db

db.connect()
db.create_tables([Account])

class AccountManager:

    def add_account(
                    self,
                    account_number: int,
                    account_name: str,
                    balance: float,
                    user_id: int,
                    currency: str
    ) -> None:
        try:
            account = Account.create(
                              account_number=account_number,
                              account_name=account_name,
                              balance=balance,
                              user_id=user_id,
                              currency=currency
            )
        except IntegrityError:
            print('Konto o podanym numerze już istnieje.')


        print(f'Konto o numerze {account_number} zostało utworzone.')
#todo walidacja danych - sprawdzenie typu, wartości, czy user_id istnieje,


if __name__ == '__main__':
    # db.connect()
    # db.create_tables([Account])
    # test = AccountManager()
    # test.add_account(1234, 'mbank', 430.0, 3, 'PLN')
    #test.add_account(1234, 'Millenium', 543, 2, 'PLN')
    # test.add_account('12', 'Dolarowe', 67, 1, 'USD')
