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