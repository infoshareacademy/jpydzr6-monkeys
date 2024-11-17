import sqlite3
from datetime import datetime

class BudgetManager:
    def __init__(self, db_name='budget.db'):
        self.db_name = db_name
        self.create_tables()

    def create_connectiion(self):
        return sqlite3.connect(self.db_name) #połączenie z bazą dannych sql

    def create_tables(self):
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

    def add_budget_entry(self, entry_type, amount, description, category="brak kategorii"):
        if entry_type not in ["income", "outcome"]:
            print("Blad: Nieprawidłowy rodzaj wpisu. Wybierz 'income' lub 'outcome'.") #Zmienić na I / O, czy zostawić pełne słowa?
            return
        if amount <= 0:
            print("Błąd. Kwota musi być dodatnią.")
            return

        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO budget (entry_type, amount, description, category, date)
            VALUES (?, ?, ?, ?, ?)
            ''', (entry_type, amount, description, category, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            print(f"Pomyślnie dodano wpis: {entry_type}, - {amount} PLN, opis: {description}, kategoria: {category}")

    def show_budget(self):
        """Wyświetla wszystkie wpisy w budżecie."""
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM budget ORDER BY date')
            rows = cursor.fetchall()
            if not rows:
                print("Brak danych - budżet jest pusty.")
                return
            for row in rows:
                print(f"{row[0]}. {row[1]}: {row[2]} PLN, {row[3]} (Kategoria: {row[4]}, Data: {row[5]})")
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
    #filtracja wszystkich wpisów
    def filter_entries(self, entry_type=None, category=None):
        return [entry for entry in self.budget if
                (entry_type is None or entry.get('type') == entry_type) and
                (category is None or entry.get('category') == category)]
    #filtracja TYLKO przychodów zamiast ogólnych wpisów
    def show_incomes_by_category(self, category):
        try:
            incomes = self.filter_entries(entry_type='income', category=category)
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
            outcomes = self.filter_entries(entry_type='outcome', category=category)
            if not outcomes:
                print(f"Brak wydatków w kategorii '{category}'.")
                return
            print(f"Lista wydatków w kategorii '{category}':")
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
