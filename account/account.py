from peewee import SqliteDatabase, Model, AutoField, BigIntegerField, CharField, IntegrityError, \
    DoesNotExist, OperationalError
from money import Currency, Monetary
import currencies

CURRENCY_MAP = {
    'EUR': currencies.EUR,
    'USD': currencies.USD,
    'PLN': currencies.PLN,
}

db = SqliteDatabase('budget.db')

class SQLError(Exception):
    pass

class Account(Model):
    DoesNotExist = None
    account_id = AutoField(primary_key=True)
    account_number = CharField(default=None, null=True)
    account_name = CharField()
    balance = BigIntegerField()
    currency_id = CharField()

    class Meta:
        database = db

db.connect()
db.create_tables([Account])

ACCOUNT_PARAMETERS ={
    '1': Account.account_number,
    '2': Account.account_name,
    '3': Account.balance,
    '4':Account.currency_id
}

 # todo rozważ dodanie wszędzie operational error (jako błąd połączenia z bazą danych)
class AccountManager:
    @staticmethod
    def add_account(
                    account_number: str,
                    account_name: str,
                    balance: int,
                    currency_id: str
    ) -> None:

        balance_int = Monetary.major_to_minor_unit(balance, CURRENCY_MAP[currency_id])
        account = Account.create(
                          account_number=account_number,
                          account_name=account_name,
                          balance=balance_int,
                          currency_id=currency_id
        )

        print(f'\nKonto o numerze zostało utworzone.')

    @staticmethod
    def delete_account(account_id: int) -> None:
        try:
            Account.delete().where(Account.account_id == account_id).execute()
        except IntegrityError:
            raise SQLError('Nie udało się usunąć konta.') from None
        print('Pomyślnie usunięto konto.')


    @staticmethod
    def edit_account(account_id: int, parameter_to_change: Account, new_value: str|Currency|Monetary) -> None:
        if parameter_to_change == Account.balance:
            currency_id = Account.select(Account.currency_id).where(Account.account_id == account_id).get().currency_id
            new_value = Monetary.major_to_minor_unit(new_value, CURRENCY_MAP[currency_id])
        Account.update({parameter_to_change: new_value}).where(Account.account_id == account_id).execute()
        #todo tu chyba trzeba dodać IntegrityError i obsługę innych błędów

    @staticmethod
    def check_record_existence(account_id: int) -> None:
        if not Account.select().where(Account.account_id == account_id).exists():
            raise SQLError('Konto o podanym ID nie istnieje')

    @staticmethod
    def check_account_number_existence(account_number: str):
        if Account.select().where(Account.account_number == account_number).exists():
            raise SQLError('Konto o podanym numerze już istnieje.')

    @staticmethod
    def show_account(account_id: int | str) -> None: # todo popraw wyświetlanie stanu konta
        if account_id:
            try:
                record = Account.select().where(Account.account_id == account_id).get()
            except DoesNotExist:
                raise SQLError('Konto o podanym ID nie istnieje.') from None

            else:
                balance = Monetary(record.balance, CURRENCY_MAP[record.currency_id])
                print(f'\nID konta: {record.account_id}\n'
                      f'Nazwa konta: {record.account_name}\n'
                      f'Numer konta: {record.account_number}\n'
                      f'Stan konta: {balance}\n')
        else:
            try:
                for record in Account:
                    balance = Monetary(record.balance, CURRENCY_MAP[record.currency_id])
                    print(f'\nID konta: {record.account_id}\n'
                          f'Nazwa konta: {record.account_name}\n'
                          f'Numer konta: {record.account_number}\n'
                          f'Stan konta: {balance}\n')
            except OperationalError:
                raise SQLError('Wystąpił problem połączenia z bazą danych.')

    @staticmethod
    def modify_balance():
        pass
