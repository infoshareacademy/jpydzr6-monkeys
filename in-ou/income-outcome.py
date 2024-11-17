import json
from datetime import datetime

class BudgetManager:
    def __init__(self, file_name='budget.json'):
        self.budget = []
        self.file_name = file_name
        self.load_budget_from_file()

    def save_budget_to_file(self):
        try:
            with open(self.file_name, 'w', encoding='utf-8') as file:
                json.dump(self.budget, file, ensure_ascii=False, indent=4)
            print("Budzet zostal zapisany do pliku.")
        except IOError:
            print("Blad: Nie udalo sie zapisac budzetu do pliku")

    def load_budget_from_file(self):
        try:
            with open(self.file_name, 'r', encoding='utf-8') as file:
                self.budget = json.load(file)
        except FileNotFoundError:
            print("Nie znaleziono pliku budżetowego.")
        except json.decoder.JSONDecodeError:
            print("Plik budżetu jest uszkodzony.")
        except IOError:
            print("Blad: Nie udalo sie wczytac pliku budzetu."

    def add_budget_entry(self, entry_type, amount, description):
        if not isinstance(amount, (int, float)) or amount <= 0:
            print("Blad: kwota musi byc liczba dodatnia.")

        entry = {
            "type": entry_type,
            "amount": amount,
            "description": description,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.budget.append(entry)
        self.save_budget_to_file()
        print(f"Pomyślnie dodano wpis: {entry_type}, - {amount} PLN, opis: {description}")

    def add_budget_entry_input(self):
        # pobiera typ wpisu ( wydatek lub przychod )
        while True:
            entry_type = input(
                "Wprowadź rodzaj wpisu ('income' dla dochodu lub 'outcome' dla wydatku, lub 'exit' aby zakończyć): ").strip().lower()
            if entry_type in ["income", "outcome"]:
                break
            elif entry_type == "exit":
                print("Zakończono dodawanie wpisu.")
                return  # kończy funkcję, gdy użytkownik wpisze "exit"
            else:
                print(
                    "Niepoprawny rodzaj wpisu. Wprowadź 'income' dla dochodu, 'outcome' dla wydatku lub 'exit' aby zakończyć.")

        # pobiera i waliduje kwote
        while True:
            try:
                amount = float(input("Wprowadź kwotę: "))
                if amount > 0:
                    break
                else:
                    print("Kwota musi być dodatnia.")
            except ValueError:
                print("Niepoprawna kwota. Upewnij się, że wprowadzasz liczbę.")

        # pobiera opis
        description = input("Wprowadź opis wpisu: ").strip()
        if not description:
            description = "Brak opisu"  # Domyślny opis, jeśli użytkownik nic nie wprowadzi

        # dodaje wpis
        self.add_budget_entry(entry_type, amount, description)

        def show_budget(self):
            if not self.budget:
                print("Brak danych - budżet jest pusty :(")
            else:
                for i, entry in enumerate(self.budget, 1):
                    print(
                        f"{i}. {entry['type']}: {entry['amount']} PLN, {entry['description']} (Data: {entry['date']})")
            # status konta ( wydatki, przychody, saldo )

        def show_budget_summary(self):
            try:
                income = sum(entry['amount'] for entry in self.budget if entry['type'] == 'income')
                expenses = sum(entry['amount'] for entry in self.budget if entry['type'] == 'outcome')
                balance = income - expenses
                print("Podsumowanie budżetu:")
                print(f" - Dochody: {income} PLN")
                print(f" - Wydatki: {expenses} PLN")
                print(f" - Saldo: {balance} PLN")
            except KeyError as e:
                print(f"Blad: brakuje klucza w danych wpisu budzetowego ({e})")

