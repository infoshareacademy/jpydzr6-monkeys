import sqlite3
import shutil
import os
from datetime import datetime
import re
from account.account import AccountManager, SQLError
from money import Monetary

class Transactions:

    def __init__(self, db_name='budget.db', table_name='operations'):
        if not re.match(r'^\w+$', table_name):  # bez znaków specjalnych w nazwie tabeli
            raise ValueError("Nazwa tabeli zawiera niedozwolone znaki.")
        self.db_name = db_name
        self.table_name = table_name
        self.transactions = []
        self.create_table()
        self.load_budget_from_file()

    def create_connection(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        with self.create_connection() as conn:
            cursor = conn.cursor()
            # Dodajemy kolumnę account_id, aby móc modyfikować saldo konta powiązanego z transakcją
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type TEXT NOT NULL,
                amount BIGINT NOT NULL,
                description TEXT,
                category TEXT,
                date TEXT NOT NULL,
                account_id INTEGER NOT NULL
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
                    ''', (entry['type'], amount_in_grosze, entry['description'], entry['category'], entry['date'], entry['account_id']))
                conn.commit()
            os.remove(backup_db)
            print("Transakcje zostały zapisane do bazy danych.")
        except Exception as e:
            print(f"Błąd podczas zapisywania transakcji: {e}")
            shutil.copyfile(backup_db, self.db_name)
            print("Przywrócono bazę danych z kopii zapasowej.")

    def load_budget_from_file(self):
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT entry_type, amount, description, category, date, account_id FROM {self.table_name}")
            rows = cursor.fetchall()
            self.transactions = [{
                'type': row[0],
                'amount': row[1] / 100,
                'description': row[2],
                'category': row[3],
                'date': row[4],
                'account_id': row[5]
            } for row in rows]
        print("Transakcje zostały załadowane z bazy danych.")

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
        # Sprawdzenie czy konto istnieje
        try:
            AccountManager.check_record_existence(account_id)
        except SQLError as e:
            errors.append(str(e))

        if errors:
            for error in errors:
                print(error)
            return

        amount_in_grosze = int(round(amount * 100))
        entry_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                INSERT INTO {self.table_name} (entry_type, amount, description, category, date, account_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (entry_type, amount_in_grosze, description, category, entry_date, account_id))
                conn.commit()

            self.load_budget_from_file()
            print(f"Pomyślnie dodano wpis: {entry_type}, - {amount:.2f}, opis: {description}, kategoria: {category}, konto: {account_id}")

            temporary_currency = { #to tylko placeholder - bez waluty
                "code": "XXX",
                "base": 10,
                "exponent": 2
            }

            minor_units = Monetary.major_to_minor_unit(amount, temporary_currency)
            transaction_monetary = Monetary(minor_units, temporary_currency)

            AccountManager.modify_balance(account_id, transaction_monetary, entry_type)

        except sqlite3.Error as e:
            print(f"Błąd podczas dodawania wpisu: {e}")
        except SQLError as e:
            print(f"Błąd podczas aktualizacji salda konta: {e}")

    def add_budget_entry_input(self):
        while True:
            entry_type = input(
                "Wprowadź rodzaj wpisu ('income' dla dochodu lub 'outcome' dla wydatku, lub 'exit' aby zakończyć): ").strip().lower() # To samo co wyżej, może warto zmienić na I/O?
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
            description = "Brak opisu" #domyślny opis

        category = input("Wprowadź kategorię wpisu: ").strip()
        if not category:
            category = "Brak kategorii" # domyślna kategoria

        self.add_budget_entry(entry_type, amount, description, category)

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
    #filtracja TYLKO przychodów zamiast ogólnych wpisów
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
    #Filtracja tylko wydatków
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

    #TYLKO PRZYCHODY
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
    #TYLKO WYDATKI
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

    def edit_budget_entry(self, index):
        try:
            entry = self.transactions[index - 1]
            print(f"Edycja wpisu: {entry['type']}: {entry['amount']:.2f} PLN, {entry['description']}")

            #Tu użytkownik wpisuje nowe dane, Value Error wystarczy czy coś więcej?
            new_type = input("Nowy typ (income/outcome): ").strip().lower()
            if new_type in ["income", "outcome"]:
                entry["type"] = new_type

            try:
                new_amount_input = input("Nowa kwota: ").strip()
                if new_amount_input:
                    new_amount = float(new_amount_input)
                    if new_amount <= 0:
                        print("Błąd: Kwota musi być dodatnia.")
                        return
                    entry["amount"] = new_amount
            except ValueError:
                print("Błąd: niepoprawna kwota. Pozostawiono starą wartość.")

            entry["description"] = input("Nowy opis: ").strip() or entry['description']
            entry["category"] = input("Nowa kategoria: ").strip() or entry.get('category', "Brak kategorii")

            # Pokazanie zmian przed zapisaniem
            print("\nProponowane zmiany:")
            print(f" - Typ: {entry['type']}")
            print(f" - Kwota: {entry['amount']:.2f} PLN")
            print(f" - Opis: {entry['description']}")
            print(f" - Kategoria: {entry['category']}")

            # Potwierdzenie zapisania zmian
            while True:
                confirm = input("Czy na pewno chcesz zapisać zmiany? (tak/nie): ").strip().lower()
                if confirm == "tak":
                    break
                elif confirm == "nie":
                    print("Edycja anulowana.")
                    return
                else:
                    print("Niepoprawny wybór. Wpisz 'tak' lub 'nie'.")

            # Aktualizacja daty i zapisanie zmian
            entry["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_budget_to_file()
            print("Wpis został zaktualizowany.")
        except IndexError:
            print("Nie znaleziono wpisu o podanym indeksie.")
        except Exception as e:
            print(f"Błąd: {e}")

    def delete_budget_entry(self, index):
        try:
            print(f"Próba usunięcia wpisu o indeksie: {index}")
            entry = self.transactions.pop(index - 1)
            self.save_budget_to_file()
            print(f"Wpis usunięty: {entry['type']} - {entry['amount']:.2f} PLN, {entry['description']}")
        except IndexError:
            print(f"Nie ma wpisu z podanym indeksem: {index}")
