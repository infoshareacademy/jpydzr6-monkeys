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
            print("Blad: Nie udalo sie wczytac pliku budzetu.")

    def add_budget_entry(self, entry_type, amount, description, category="brak kategorii"):
        if entry_type not in ["income", "outcome"]:
            print("Blad: Nieprawidłowy rodzaj wpisu. Wybierz 'income' lub 'outcome'.")
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

    def add_budget_entry_input(self):
        while True:
            entry_type = input(
                "Wprowadź rodzaj wpisu ('income' dla dochodu lub 'outcome' dla wydatku, lub 'exit' aby zakończyć): ").strip().lower()
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
            description = "Brak opisu"

        category = input("Wprowadz kategorię wpisu: ").strip()
        if not category:
            category = "Brak kategorii"

        self.add_budget_entry(entry_type, amount, description, category)

    def show_budget(self):
        if not self.budget:
            print("Brak danych - budżet jest pusty :(")
        else:
            sorted_budget = sorted(self.budget, key=lambda x: x['date'])
            for i, entry in enumerate(sorted_budget, 1):
                #kategorie - nie wiem czy tak zadziała :(
                category = entry.get('category', 'Brak kategorii')
                print(f"{i}. {entry['type']}: {entry['amount']} PLN, {entry['description']} "
                      f"(Kategoria: {category}, (Data: {entry['date']})")

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

    def edit_budget_entry(self, index):
        try:
            entry = self.budget[index - 1]
            print(f"Edycja wpisu: {entry['type']}: {entry['amount']} PLN, {entry['description']}")
            entry["type"] = input("Nowy typ (income/outcome): ").strip().lower() or entry['type']
            entry["amount"] = input("Nowa kwota: ").strip() or entry['amount']
            entry["description"] = input("Nowy opis: ").strip() or entry['description']
            entry["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_budget_to_file()
            print("Wpis zostal zaktualizowany")
        except IndexError:
            print("Nie znaleziono pliku o podanym indeksie. ")
        except ValueError:
            print("Błąd: niepoprawna kwota")

    def delete_budget_entry(self, index):
        try:
            entry = self.budget.pop(index - 1)
            self.save_budget_to_file()
            print(f"Wpis usunięty: {entry['type']} - {entry['amount']} PLN, {entry['description']}")
        except IndexError:
            print("Nie ma wpisu z podanym indexem.")