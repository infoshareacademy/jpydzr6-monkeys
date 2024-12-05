import sqlite3
from datetime import datetime
from money import Monetary, Currency


class BudgetManager:
    def __init__(self, currency: Currency, db_name='budget.db'):
        self.db_name = db_name
        self.budget = []
        self.create_table()
        self.load_budget_from_file()
        self.__entry_types = ('income', 'outcome')
        self.__currency = currency

    def create_connection(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type TEXT NOT NULL,
                amount BIGINT NOT NULL,
                description TEXT,
                category TEXT,
                date TEXT NOT NULL
            )
            ''')
            conn.commit()

    def save_budget_to_file(self):
        #integracja z sqlitem - zapisuje dane do bazy
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budget")  # Usuwa stare dane
            for entry in self.budget:
                cursor.execute('''
                INSERT INTO budget (entry_type, amount, description, category, date)
                VALUES (?, ?, ?, ?, ?)
                ''', (entry['type'], entry['amount'], entry['description'], entry['category'], entry['date']))
            conn.commit()
        print("Budżet został zapisany do bazy danych.")

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

    def add_budget_entry(self, entry_type: str, entry: Monetary, description: str, category: str="brak kategorii") -> None:
        if entry_type not in self.__entry_types:
            print("Blad: Nieprawidłowy rodzaj wpisu. Wybierz 'income' lub 'outcome'.") #Zmienić na I / O, czy zostawić pełne słowa?
            return
        if not isinstance(entry, Monetary):
            print("Blad: Wpis jest złego typu danych")
            return
        if entry.amount < 0:
            print("Blad: Kwota musi być liczbą nieujemną.")
            return
        if len(description) > 255:
            print("Blad: Opis jest za długi (maksymalnie 255 znaków).")
            return

        record = {
            "type": entry_type,
            "amount": entry.amount,
            "description": description,
            "category": category,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.budget.append(record)
        self.save_budget_to_file()
        print(f"Pomyślnie dodano wpis: {entry_type} - {entry}, opis: {description}, kategoria: {category}")

    def add_budget_entry_input(self): #Dodawanie wpisów z inputem, również do usunięcia w przyszłości.
        while True:
            entry_type = input(
                "Wprowadź rodzaj wpisu ('income' dla dochodu lub 'outcome' dla wydatku, lub 'exit' aby zakończyć): ").strip().lower() # To samo co wyżej, może warto zmienić na I/O?
            if entry_type in self.__entry_types:
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

        amount = Monetary.major_to_minor_unit(amount, self.__currency)
        amount = Monetary(amount, self.__currency)
        self.add_budget_entry(entry_type, amount, description, category)

    def show_budget(self):
        if not self.budget:
            print("Brak danych - budżet jest pusty. ")
        else:
            sorted_budget = sorted(self.budget, key=lambda x: x['date'])
            for i, entry in enumerate(sorted_budget, 1):
                category = entry.get('category', 'Brak kategorii')
                amount = Monetary(entry['amount'], self.__currency)
                print(f"{i}. {entry['type']}: {amount}, {entry['description']} "
                      f"(Kategoria: {category}, Data: {entry['date']})")
        # status konta ( wydatki, przychody, saldo )
    def show_budget_summary(self):
        if not self.budget:
            print("Brak danych do podsumowania.")
            return
        try:
            incomes = sum(entry['amount'] for entry in self.budget if entry['type'] == 'income')
            expenses = sum(entry['amount'] for entry in self.budget if entry['type'] == 'outcome')
            incomes = Monetary(incomes, self.__currency)
            expenses = Monetary(expenses, self.__currency)
            balance = incomes - expenses
            print("Podsumowanie budżetu:")
            print(f" - Dochody: {incomes}")
            print(f" - Wydatki: {expenses}")
            print(f" - Saldo: {balance}")
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
                entry_monetary = Monetary(entry['amount'], self.__currency)
                print(f"{i}. Kwota: {entry_monetary}, Opis: {entry['description']}, Data: {entry['date']}")
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
                entry_monetary = Monetary(entry['amount'], self.__currency)
                print(f"{i}. Kwota: {entry_monetary}, Opis: {entry['description']}, Data: {entry['date']}")
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
                entry_monetary = Monetary(entry['amount'], self.__currency)
                print(f"{i}. Kwota: {entry_monetary}, Opis: {entry['description']}, Kategoria: "
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
                entry_monetary = Monetary(entry['amount'], self.__currency)
                print(f"{i}. Kwota: {entry_monetary}, Opis: {entry['description']}, "
                      f"Kategoria: {entry.get('category', 'Brak kategorii')}, Data: {entry['date']}")
        except KeyError as e:
            print(f"Błąd: Brakuje klucza w danych budżetu ({e}).")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")

    def edit_budget_entry(self, index):
        try:
            entry = self.budget[index - 1]
            entry_monetary = Monetary(entry['amount'], self.__currency)
            print(f"Edycja wpisu: {entry['type']}: {entry_monetary}, {entry['description']}")

            #Tu użytkownik wpisuje nowe dane, Value Error wystarczy czy coś więcej?
            new_type = input("Nowy typ (income/outcome): ").strip().lower()
            if new_type in ["income", "outcome"]:
                entry["type"] = new_type

            try:
                new_amount = input("Nowa kwota: ").strip()
                if new_amount:
                    new_amount = float(new_amount)
                    new_amount = Monetary.major_to_minor_unit(new_amount, self.__currency)
                    new_amount = Monetary(new_amount, self.__currency)
            except ValueError:
                print("Błąd: niepoprawna kwota. Pozostawiono starą wartość.")

            entry["description"] = input("Nowy opis: ").strip() or entry['description']
            entry["category"] = input("Nowa kategoria: ").strip() or entry.get('category', "Brak kategorii")

            # Pokazanie zmian przed zapisaniem
            print("\nProponowane zmiany:")
            print(f" - Typ: {entry['type']}")
            print(f" - Kwota: {new_amount}")
            print(f" - Opis: {entry['description']}")
            print(f" - Kategoria: {entry['category']}")

            # Potwierdzenie zapisania zmian
            confirm = input("Czy na pewno chcesz zapisać zmiany? (tak/nie): ").strip().lower()
            if confirm != "tak":
                print("Edycja anulowana.")
                return
            entry["amount"] = new_amount.amount
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
            entry_monetary = Monetary(entry['amount'], self.__currency)
            self.save_budget_to_file()
            print(f"Wpis usunięty: {entry['type']} - {entry_monetary}, {entry['description']}")
        except IndexError:
            print(f"Nie ma wpisu z podanym indeksem: {index}")
