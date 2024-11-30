from peewee import SqliteDatabase, Model, AutoField, BigIntegerField, CharField, DecimalField, IntegrityError

db = SqliteDatabase('budget.db')


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
            print('Konto o podanym numerze już istnieje.')
        else:
            print(f'Konto o numerze {account_number} zostało utworzone.')

    @staticmethod
    def edit_account(account_id: int, parameter_to_change: str, new_value: str) -> None:
        try:
            field = getattr(Account, parameter_to_change, None)
        except ValueError:
            raise SQLError('Nieprawdiłowo określono atrybut do zmiany.')
        Account.update({field: new_value}).where(Account.account_id == account_id).execute()

if __name__ == '__main__':
    # AccountManager().add_account('1234', 'nowe', 321, 1, 'PLN')
    AccountManager().edit_account(1, 'balances', 0)