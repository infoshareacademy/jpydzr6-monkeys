from peewee import SqliteDatabase, Model, AutoField, BigIntegerField, CharField, DecimalField, IntegrityError, \
    DoesNotExist

db = SqliteDatabase('budget.db')

class SQLError(Exception):
    pass

class Account(Model):
    DoesNotExist = None
    account_id = AutoField()
    account_number = CharField(unique=True)
    account_name = CharField()
    balance = DecimalField(decimal_places=2)
    user_id = BigIntegerField()
    currency_id = CharField()

    class Meta:
        database = db

db.connect()
db.create_tables([Account])

class AccountManager:

    def add_account(
                    self,
                    account_number: str,
                    account_name: str,
                    balance: float,
                    user_id: int,
                    currency_id: str
    ) -> None:
        try:
            account = Account.create(
                              account_number=account_number,
                              account_name=account_name,
                              balance=balance,
                              user_id=user_id,
                              currency_id=currency_id
            )
        except IntegrityError:
            raise SQLError('Konto o podanym numerze już istnieje.') from None
        else:
            print(f'Konto o numerze {account_number} zostało utworzone.')

    def delete_account(account_number: str) -> None:
        try:
            Account.delete().where(Account.account_number == account_number)
        except DoesNotExist:
            raise SQLError('Konto o podanym numerze nie istnieje.') from None
