import json #JSONow nie traktujcie na powaznie - w tej chwili sluza jedynie do sprawdzenia poprawnosci zapisywania ( działa jbc )
from datetime import datetime

class BudgetManager:
    def __init__(self, file_name='budget.json'):
        self.budget = []
        self.file_name = file_name
        self.load_budget_from_file()

    def save_budget_to_file(self):
        try:
            with open(self.file_name, 'w', encoding='utf-8') as file:
                json.dump(self.budget, file, ensure_ascii=False, indent=4) #Do usunięcia w przyszłości
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

    def show_entries_by_category(self, category):
        filtered_entries = [entry for entry in self.budget if entry.get('category') == category]
        if not filtered_entries:
            print(f"Brak wpisów dla podanej kategorii '{category}'")
        else:
            for i, entry in enumerate(filtered_entries, 1):
                print(f"{i}. {entry['type']}: {entry['amount']} PLN, {entry['description']} "
                      f"(Kategoria: {category}, Data: {entry['date']})")

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
