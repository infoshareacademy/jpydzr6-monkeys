import os
import re
import shutil
import sqlite3
from datetime import datetime
from peewee import IntegrityError, Model, CharField, BigIntegerField, ForeignKeyField
from account import AccountManager, SQLError, db, Account, CURRENCY_MAP
from money import Monetary


class Operations(Model):
    DoesNotExist = None
    entry_type = CharField()
    amount = BigIntegerField()
    description = CharField(null=True)
    category = CharField(null=True)
    date = CharField()
    account_id = ForeignKeyField(Account, backref='operations', on_delete='CASCADE')

    class Meta:
        database = db


class Transactions:
    def __init__(self, db_name='operations.db', table_name='operations'):
        if not re.match(r'^\w+$', table_name):  # bez znaków specjalnych w nazwie tabeli
            raise ValueError("Nazwa tabeli zawiera niedozwolone znaki.")
        self.db_name = db_name
        self.table_name = table_name
        self.transactions = []
        self.load_budget_from_file()

    def create_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def create_table(self):
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type TEXT NOT NULL,
                amount BIGINT NOT NULL,
                description TEXT,
                category TEXT,
                date TEXT NOT NULL,
                account_id INTEGER NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
            ''')
            conn.commit()

    def save_budget_to_file(self):
        backup_db = self.db_name + '.bak'
        try:
            if os.path.exists(self.db_name):
                shutil.copyfile(self.db_name, backup_db)
                print("Kopia zapasowa bazy danych została utworzona.")
            else:
                print("Plik bazy danych nie istnieje. Kopia zapasowa nie została utworzona.")

            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('BEGIN TRANSACTION;')
                cursor.execute(f"DELETE FROM {self.table_name}")

                for entry in self.transactions:
                    amount_in_grosze = int(round(entry['amount'] * 100))
                    cursor.execute(f'''
                    INSERT INTO {self.table_name} (entry_type, amount, description, category, date, account_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (entry['type'], amount_in_grosze, entry['description'], entry['category'], entry['date'],
                          entry['account_id']))
                conn.commit()
            os.remove(backup_db)
            print("Transakcje zostały zapisane do bazy danych.")
        except Exception as e:
            print(f"Błąd podczas zapisywania transakcji: {e}")
            shutil.copyfile(backup_db, self.db_name)
            print("Przywrócono bazę danych z kopii zapasowej.")

    def load_budget_from_file(self):
        try:
            rows = Operations.select()
            self.transactions = [{
                'type': row.entry_type,
                'amount': row.amount / 100,
                'description': row.description,
                'category': row.category,
                'date': row.date,
                'account_id': row.account_id.account_id
            } for row in rows]
            print(f"Załadowano transakcje: {self.transactions}")
        except Exception as e:
            print(f"Błąd podczas ładowania danych: {e}")

    GENERIC_CURRENCY = {
        "code": "XXX",
        "base": 10,
        "exponent": 2
    }

    def add_budget_entry(self, account_id, entry_type, amount, description, category="brak kategorii"):
        errors = []

        if entry_type not in ["income", "outcome"]:
            errors.append("Błąd: Nieprawidłowy rodzaj wpisu. Wybierz 'income' lub 'outcome'.")

        try:
            amount = float(amount)
            if amount <= 0:
                errors.append("Błąd: Kwota musi być dodatnia.")
        except ValueError:
            errors.append("Błąd: Kwota musi być liczbą.")

        if len(description) > 255:
            errors.append("Błąd: Opis jest za długi (maksymalnie 255 znaków).")

        try:
            AccountManager.check_record_existence(account_id)
        except SQLError as e:
            errors.append(str(e))

        if errors:
            for error in errors:
                print(error)
            return

        amount_in_grosze = int(round(amount * 100))
        try:
            account = Account.get(Account.account_id == account_id)
            currency_code = account.currency_id
            transaction_currency = CURRENCY_MAP[currency_code]

            Operations.create(
                entry_type=entry_type,
                amount=amount_in_grosze,
                description=description,
                category=category,
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                account_id=account_id
            )

            transaction_monetary = Monetary(amount_in_grosze, transaction_currency)
            AccountManager.modify_balance(account_id, transaction_monetary, entry_type)

            print(
                f"Pomyślnie dodano wpis: {entry_type}, {amount:.2f} PLN, {description}, {category}, konto: {account_id}"
            )

        except IntegrityError as e:
            print(f"Błąd: Wystąpił problem z bazą danych: {e}")
        except SQLError as e:
            print(f"Błąd podczas aktualizacji salda konta: {e}")
        except KeyError as e:
            print(f"Błąd: Nie znaleziono waluty w mapowaniu CURRENCY_MAP: {e}")

    def add_budget_entry_input(self, account_id=None):
        while True:
            entry_type = input(
                "Wprowadź rodzaj wpisu ('income' dla dochodu lub 'outcome' dla wydatku, lub 'exit' aby zakończyć): ").strip().lower()  # To samo co wyżej, może warto zmienić na I/O?
            if entry_type in ["income", "outcome"]:
                break
            elif entry_type == "exit":
                print("Zakończono dodawanie wpisu.")
                return
            else:
                print("Niepoprawny rodzaj wpisu. Spróbuj ponownie.")

        while True:
            try:
                amount = float(input("Wprowadź kwotę: "))
                if amount > 0:
                    break
                else:
                    print("Kwota musi być dodatnia.")
            except ValueError:
                print("Niepoprawna kwota. Upewnij się, że wprowadzasz liczbę.")

        description = input("Wprowadź opis wpisu: ").strip()
        if not description:
            description = "Brak opisu"  # domyślny opis

        category = input("Wprowadź kategorię wpisu: ").strip()
        if not category:
            category = "Brak kategorii"  # domyślna kategoria

        self.add_budget_entry(account_id, entry_type, amount, description, category)

    def show_budget(self):
        if not self.transactions:
            print("Brak danych - lista jest pusta. ")
        else:
            sorted_budget = sorted(self.transactions, key=lambda x: x['date'])
            for i, entry in enumerate(sorted_budget, 1):
                category = entry.get('category', 'Brak kategorii')
                print(f"{i}. {entry['type']}: {entry['amount']:.2f} PLN, {entry['description']} "
                      f"(Kategoria: {category}, Data: {entry['date']})")
        # status konta ( wydatki, przychody, saldo )

    def show_budget_summary(self):
        if not self.transactions:
            print("Brak danych do podsumowania.")
            return
        try:
            income = sum(entry['amount'] for entry in self.transactions if entry['type'] == 'income')
            expenses = sum(entry['amount'] for entry in self.transactions if entry['type'] == 'outcome')
            balance = income - expenses
            print("Podsumowanie transakcji:")
            print(f" - Dochody: {income:.2f} PLN")
            print(f" - Wydatki: {expenses:.2f} PLN")
            print(f" - Saldo: {balance:.2f} PLN")
        except KeyError as e:
            print(f"Błąd: brakuje klucza w danych wpisu budżetowego ({e})")

    # filtracja TYLKO przychodów zamiast ogólnych wpisów
    def show_incomes_by_category(self, category):
        try:
            incomes = [entry for entry in self.transactions if
                       entry.get('type') == 'income' and entry.get('category') == category]
            if not incomes:
                print(f"Brak dochodów w kategorii '{category}'.")
                return
            print(f"Lista dochodów w kategorii '{category}':")
            for i, entry in enumerate(incomes, 1):
                print(f"{i}. Kwota: {entry['amount']:.2f} PLN, Opis: {entry['description']}, Data: {entry['date']}")
        except KeyError as e:
            print(f"Błąd: Brakuje klucza w danych transakcji: ({e}).")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")

    # Filtracja tylko wydatków
    def show_outcomes_by_category(self, category):
        try:
            outcomes = [entry for entry in self.transactions if
                        entry.get('type') == 'outcome' and entry.get('category') == category]
            if not outcomes:
                print(f"Brak wydatków w kategorii '{category}'.")
                return
            print(f"Lista wydatków w kategorii '{category}':")
            for i, entry in enumerate(outcomes, 1):
                print(f"{i}. Kwota: {entry['amount']:.2f} PLN, Opis: {entry['description']}, Data: {entry['date']}")
        except KeyError as e:
            print(f"Błąd: Brakuje klucza w danych transakcji ({e}).")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")

    # TYLKO PRZYCHODY
    def show_incomes(self):
        try:
            incomes = [entry for entry in self.transactions if entry.get('type') == 'income']
            if not incomes:
                print("Brak dochodów do wyświetlenia")
                return
            print("Lista dochodów: ")
            for i, entry in enumerate(incomes, 1):
                print(f"{i}. Kwota: {entry['amount']:.2f} PLN, Opis: {entry['description']}, Kategoria: "
                      f"{entry.get('category', 'Brak kategorii')}, Data: {entry['date']}")
        except KeyError as e:
            print(f"Błąd: Brakuje klucza w danych transakcji ({e}). ")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")

    # TYLKO WYDATKI
    def show_outcomes(self):
        try:
            outcomes = [entry for entry in self.transactions if entry.get('type') == 'outcome']
            if not outcomes:
                print("Brak wydatków do wyświetlenia")
                return
            print("Lista wydatków: ")
            for i, entry in enumerate(outcomes, 1):
                print(f"{i}. Kwota: {entry['amount']:.2f} PLN, Opis: {entry['description']}, "
                      f"Kategoria: {entry.get('category', 'Brak kategorii')}, Data: {entry['date']}")
        except KeyError as e:
            print(f"Błąd: Brakuje klucza w danych transakcji: ({e}).")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")

    def edit_budget_entry(self, entry_id, new_entry_type=None, new_amount=None, new_description=None,
                          new_category=None):
        try:
            entry = Operations.get_by_id(entry_id)
            print(
                f"Edycja wpisu: {entry.entry_type} - {entry.amount / 100:.2f} PLN, {entry.description}, {entry.category}")

            old_type = entry.entry_type
            old_amount = entry.amount
            account_id = entry.account_id.account_id

            if new_entry_type and new_entry_type in ["income", "outcome"]:
                entry.entry_type = new_entry_type
            else:
                print("Nie zmieniono typu wpisu lub podano nieprawidłowy typ.")

            if new_amount is not None:
                try:
                    new_amount_grosze = int(round(float(new_amount) * 100))
                    if new_amount_grosze > 0:
                        entry.amount = new_amount_grosze
                    else:
                        print("Kwota musi być dodatnia. Nie zmieniono wartości.")
                except ValueError:
                    print("Niepoprawna kwota. Nie zmieniono wartości.")

            if new_description:
                entry.description = new_description

            if new_category:
                entry.category = new_category

            entry.save()

            balance_difference = 0
            if old_type == 'income':
                balance_difference -= old_amount
            elif old_type == 'outcome':
                balance_difference += old_amount

            if entry.entry_type == 'income':
                balance_difference += entry.amount
            elif entry.entry_type == 'outcome':
                balance_difference -= entry.amount

            from money import Monetary
            transaction_monetary = Monetary(abs(balance_difference), {"code": "XXX", "base": 10, "exponent": 2})

            if balance_difference > 0:
                AccountManager.modify_balance(account_id, transaction_monetary, 'income')
            elif balance_difference < 0:
                AccountManager.modify_balance(account_id, transaction_monetary, 'outcome')

            self.load_budget_from_file()
            print("Wpis został zaktualizowany i saldo konta zostało zmodyfikowane.")

        except Operations.DoesNotExist:
            print(f"Nie znaleziono wpisu o ID: {entry_id}")
        except Exception as e:
            print(f"Błąd podczas edycji wpisu: {e}")

    def delete_budget_entry(self, entry_id):
        try:
            entry = Operations.get_by_id(entry_id)
            account_id = entry.account_id.account_id  # Użycie poprawnego klucza obcego
            amount_in_grosze = entry.amount
            transaction_type = entry.entry_type

            entry.delete_instance()

            # Aktualizacja salda na koncie
            transaction_monetary = Monetary(amount_in_grosze, {"code": "XXX", "base": 10, "exponent": 2})
            if transaction_type == 'income':
                AccountManager.modify_balance(account_id, transaction_monetary, 'outcome')
            elif transaction_type == 'outcome':
                AccountManager.modify_balance(account_id, transaction_monetary, 'income')

            self.load_budget_from_file()
            print(f"Wpis został pomyślnie usunięty.")
        except Operations.DoesNotExist:
            print(f"Nie znaleziono wpisu o ID: {entry_id}")
        except Exception as e:
            print(f"Błąd podczas usuwania wpisu: {e}")