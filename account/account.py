from peewee import SqliteDatabase, Model, AutoField, BigIntegerField, CharField, DecimalField, IntegrityError, \
    DoesNotExist, OperationalError

db = SqliteDatabase('budget.db')

class SQLError(Exception):
    pass

class Account(Model):
    DoesNotExist = None
    account_id = AutoField(primary_key=True)
    account_number = CharField(unique=True)
    account_name = CharField()
    balance = DecimalField(decimal_places=2)
    user_id = BigIntegerField()
    currency_id = CharField()

    class Meta:
        database = db

db.connect()
db.create_tables([Account])

ACCOUNT_PARAMETERS ={
    '1': Account.account_number,
    '2': Account.account_name,
    '3': Account.balance,
    '4': Account.user_id,
    '5':Account.currency_id
}


class AccountManager:
    @staticmethod
    def add_account(
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
            print(f'\nKonto o numerze {account_number} zostało utworzone.')

    @staticmethod
    def delete_account(account_id: str) -> None: # todo przyjrzyj się temu typowaniu
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
    def edit_account(account_id: int, parameter_to_change: str, new_value: str|int|float) -> None:
        Account.update({parameter_to_change: new_value}).where(Account.account_id == account_id).execute()
        #todo tu chyba trzeba dodać IntegrityError

    @staticmethod
    def check_record_existence(account_id: int) -> None:
        if not Account.select().where(Account.account_id == account_id).exists():
            raise SQLError('Konto o podanym ID nie istnieje')

    @staticmethod
    def show_account(account_id: str) -> None: #todo pogadaj z markiem o przekazywaniu str albo int czy warto robić walidację
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
