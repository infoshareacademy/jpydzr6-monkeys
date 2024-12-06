from peewee import SqliteDatabase, Model, AutoField, BigIntegerField, CharField, IntegrityError, \
    DoesNotExist, OperationalError
from money import Currency, Monetary
import currencies

db = SqliteDatabase('budget.db')

class SQLError(Exception):
    pass

class Account(Model):
    DoesNotExist = None
    account_id = AutoField(primary_key=True)
    account_number = CharField(unique=True)
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
    '4':Account.currency_id # todo upewnij się, że tu wsyzstko gra
}

 # todo rozważ dodanie wszędzie operational error (jako błądz połączenia z bazą danych
class AccountManager:
    @staticmethod
    def add_account(
                    account_number: str,
                    account_name: str,
                    balance: Monetary,
                    currency_id: Currency
    ) -> None:
        try:
            account = Account.create(
                              account_number=account_number,
                              account_name=account_name,
                              balance=balance,
                              currency_id=currency_id
            )
        except IntegrityError:
            raise SQLError('Konto o podanym numerze już istnieje.') from None
        else:
            print(f'\nKonto o numerze {account_number} zostało utworzone.')

    @staticmethod
    def delete_account(account_id: str) -> None: # todo przyjrzyj się temu typowaniu
        # todo zastosuj tutaj na starcie sprawdzenie czy dany rekord istnieje
        try:
            query = Account.delete().where(Account.account_id == account_id)
            if query.execute():
                print('Pomyślnie usunięto konto.')
            else:
                raise SQLError('Konto o podanym numerze ID nie istnieje.') from None
        except IntegrityError:
            raise SQLError('Nie udało się usunąć konta.') from None
        except ValueError:
            raise SQLError('Podana nowa wartość jest nieprawidłowa.') from None
        # todo tutaj nie ma nowej wartości :O skąd ten ValueError

    @staticmethod
    def edit_account(account_id: int, parameter_to_change: str, new_value: str|Currency|Monetary) -> None:
        Account.update({parameter_to_change: new_value}).where(Account.account_id == account_id).execute()
        #todo tu chyba trzeba dodać IntegrityError i obsługę innych błędów

    @staticmethod
    def check_record_existence(account_id: int) -> None:
        if not Account.select().where(Account.account_id == account_id).exists():
            raise SQLError('Konto o podanym ID nie istnieje')

    @staticmethod
    def show_account(account_id: str) -> None:
        if account_id:
            try:
                record = Account.select().where(Account.account_id == account_id).get()
            except DoesNotExist:
                raise SQLError('Konto o podanym ID nie istnieje.') from None

            else:
                print(f'\nID konta: {record.account_id}\n'
                      f'Nazwa konta: {record.account_name}\n'
                      f'Numer konta: {record.account_number}\n'
                      f'Stan konta: {record.balance} {record.currency_id}\n')
        else:
            try:
                for record in Account:
                    print(f'\nID konta: {record.account_id}\n'
                          f'Nazwa konta: {record.account_name}\n'
                          f'Numer konta: {record.account_number}\n'
                          f'Stan konta: {record.balance} {record.currency_id}\n')
            except OperationalError:
                raise SQLError('Wystąpił problem połączenia z bazą danych.')

if __name__ == '__main__':
    AccountManager.add_account('1234', 'z monetary dwa', 456, 'PLN')