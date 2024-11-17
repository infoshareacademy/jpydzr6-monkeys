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