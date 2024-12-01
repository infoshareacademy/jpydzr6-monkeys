import sqlite3
import shutil
import os
from datetime import datetime

class Transactions:
    def __init__(self, db_name='budget.db'):
        self.db_name = db_name
        self.budget = []
        self.create_table()
        self.load_budget_from_file()

    def create_connection(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                category TEXT,
                date TEXT NOT NULL
            )
            ''')
            conn.commit()

    def save_budget_to_file(self):
        # Integracja z SQLite - zapisuje dane do bazy
        backup_db = self.db_name + '.bak'
        try:
            # Tworzenie kopii zapasowej bazy danych
            shutil.copyfile(self.db_name, backup_db)
            print("Kopia zapasowa bazy danych została utworzona.")

            with self.create_connection() as conn:
                cursor = conn.cursor()
                # Rozpoczęcie transakcji
                cursor.execute('BEGIN TRANSACTION;')
                # Usunięcie starych danych
                cursor.execute("DELETE FROM budget")
                # Wstawienie nowych danych
                for entry in self.budget:
                    cursor.execute('''
                    INSERT INTO budget (entry_type, amount, description, category, date)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (entry['type'], entry['amount'], entry['description'], entry['category'], entry['date']))
                # Zatwierdzenie transakcji
                conn.commit()
            # Usunięcie kopii zapasowej po pomyślnym zapisie
            os.remove(backup_db)
            print("Budżet został zapisany do bazy danych.")
        except Exception as e:
            print(f"Błąd podczas zapisywania budżetu: {e}")
            # Przywrócenie bazy danych z kopii zapasowej
            shutil.copyfile(backup_db, self.db_name)
            print("Przywrócono bazę danych z kopii zapasowej.")

    def load_budget_from_file(self):
        #integracja z sqlitem - pobiera dane z bazy
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entry_type, amount, description, category, date FROM budget")
            rows = cursor.fetchall()
            self.budget = [{
                'type': row[0],
                'amount': row[1],
                'description': row[2],
                'category': row[3],
                'date': row[4]
            } for row in rows]
        print("Budżet został załadowany z bazy danych.")

    def add_budget_entry(self, entry_type, amount, description, category="brak kategorii"):
        if entry_type not in ["income", "outcome"]:
            print("Blad: Nieprawidłowy rodzaj wpisu. Wybierz 'income' lub 'outcome'.") #Zmienić na I / O, czy zostawić pełne słowa?
            return
        if not isinstance(amount, (int, float)) or amount <= 0:
            print("Blad: Kwota musi być liczbą dodatnią.")
            return
        if len(description) > 255:
            print("Blad: Opis jest za długi (maksymalnie 255 znaków).")
            return

        entry = {
            "type": entry_type,
            "amount": amount,
            "description": description,
            "category": category,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.budget.append(entry)
        self.save_budget_to_file()
        print(f"Pomyślnie dodano wpis: {entry_type}, - {amount} PLN, opis: {description}, kategoria: {category}")

    def add_budget_entry_input(self): #Dodawanie wpisów z inputem, również do usunięcia w przyszłości.
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

        category = input("Wprowadz kategorię wpisu: ").strip()
        if not category:
            category = "Brak kategorii" # domyśla kategoria

        self.add_budget_entry(entry_type, amount, description, category)

    def show_budget(self):
        if not self.budget:
            print("Brak danych - budżet jest pusty. ")
        else:
            sorted_budget = sorted(self.budget, key=lambda x: x['date'])
            for i, entry in enumerate(sorted_budget, 1):
                category = entry.get('category', 'Brak kategorii')
                print(f"{i}. {entry['type']}: {entry['amount']} PLN, {entry['description']} "
                      f"(Kategoria: {category}, Data: {entry['date']})")
        # status konta ( wydatki, przychody, saldo )
    def show_budget_summary(self):
        if not self.budget:
            print("Brak danych do podsumowania.")
            return
        try:
            income = sum(entry['amount'] for entry in self.budget if entry['type'] == 'income')
            expenses = sum(entry['amount'] for entry in self.budget if entry['type'] == 'outcome')
            balance = income - expenses
            print("Podsumowanie budżetu:")
            print(f" - Dochody: {income:.2f} PLN")
            print(f" - Wydatki: {expenses:.2f} PLN")
            print(f" - Saldo: {balance:.2f} PLN")
        except KeyError as e:
            print(f"Blad: brakuje klucza w danych wpisu budzetowego ({e})")
    #filtracja TYLKO przychodów zamiast ogólnych wpisów
    def show_incomes_by_category(self, category):
        try:
            incomes = [entry for entry in self.budget if
                       entry.get('type') == 'income' and entry.get('category') == category]
            if not incomes:
                print(f"Brak dochodów w kategorii '{category}'.")
                return
            print(f"Lista dochodów w kategorii '{category}':")
            for i, entry in enumerate(incomes, 1):
                print(f"{i}. Kwota: {entry['amount']} PLN, Opis: {entry['description']}, Data: {entry['date']}")
        except KeyError as e:
            print(f"Błąd: Brakuje klucza w danych budżetu ({e}).")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")
    #Filtracja tylko wydatków
    def show_outcomes_by_category(self, category):
        try:
            outcomes = [entry for entry in self.budget if
                       entry.get('type') == 'outcome' and entry.get('category') == category]
            if not outcomes:
                print(f"Brak wydatków w kategorii '{category}'.")
                return
            print(f"Lista wydatków w kategorii '{category}:")
            for i, entry in enumerate(outcomes, 1):
                print(f"{i}. Kwota: {entry['amount']} PLN, Opis: {entry['description']}, Data: {entry['date']}")
        except KeyError as e:
            print(f"Błąd: Brakuje klucza w danych budżetu ({e}).")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")

    #TYLKO PRZYCHODY
    def show_incomes(self):
        try:
            incomes = [entry for entry in self.budget if entry.get('type') == 'income']
            if not incomes:
                print("Brak dochodów do wyświetlenia")
                return
            print("Lista dochodów: ")
            for i, entry in enumerate(incomes, 1):
                print(f"{i}. Kwota: {entry['amount']} PLN, Opis: {entry['description']}, Kategoria: "
                      f"{entry.get('category', 'Brak kategorii')}, Data: {entry['date']}")
        except KeyError as e:
            print(f"Błąd: Brakuje klucza w danych budżetu ({e}). ")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")
    #TYLKO WYDATKI
    def show_outcomes(self):
        try:
            outcomes = [entry for entry in self.budget if entry.get('type') == 'outcome']
            if not outcomes:
                print("Brak wydatków do wyświetlenia")
                return
            print("Lista wydatków: ")
            for i, entry in enumerate(outcomes, 1):
                print(f"{i}. Kwota: {entry['amount']} PLN, Opis: {entry['description']}, "
                      f"Kategoria: {entry.get('category', 'Brak kategorii')}, Data: {entry['date']}")
        except KeyError as e:
            print(f"Błąd: Brakuje klucza w danych budżetu ({e}).")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")

    def edit_budget_entry(self, index):
        try:
            entry = self.budget[index - 1]
            print(f"Edycja wpisu: {entry['type']}: {entry['amount']} PLN, {entry['description']}")

            #Tu użytkownik wpisuje nowe dane, Value Error wystarczy czy coś więcej?
            new_type = input("Nowy typ (income/outcome): ").strip().lower()
            if new_type in ["income", "outcome"]:
                entry["type"] = new_type

            try:
                new_amount = input("Nowa kwota: ").strip()
                if new_amount:
                    entry["amount"] = float(new_amount)
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
            confirm = input("Czy na pewno chcesz zapisać zmiany? (tak/nie): ").strip().lower()
            if confirm != "tak":
                print("Edycja anulowana.")
                return

            # Aktualizacja daty i zapisanie zmian
            entry["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_budget_to_file()
            print("Wpis został zaktualizowany.")
        except IndexError:
            print("Nie znaleziono wpisu o podanym indeksie.")
        except Exception as e:
            print(f"Błąd: {e}")

    #usuwanie wpisow prawdopodobnie do poprawienia, ale jeszcze nie wiem w jaki sposób
    def delete_budget_entry(self, index):
        try:
            print(f"Próba usunięcia wpisu o indeksie: {index}")
            entry = self.budget.pop(index - 1)
            self.save_budget_to_file()
            print(f"Wpis usunięty: {entry['type']} - {entry['amount']} PLN, {entry['description']}")
        except IndexError:
            print(f"Nie ma wpisu z podanym indeksem: {index}")


if __name__ == '__main__':
    manager = Transactions()

    manager.add_budget_entry('income', 350, 'Wynagrodzenie', 'Praca')
    manager.add_budget_entry('outcome', 40, 'Zakupy spożywcze', 'Jedzenie')

print("\n--- Lista dochodów ---")
manager.show_incomes()
print("\n--- Lista wydatków ---")
manager.show_outcomes()