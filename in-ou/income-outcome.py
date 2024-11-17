import sqlite3
from datetime import datetime

class BudgetManager:
    def __init__(self, db_name='budget.db'):
        self.db_name = db_name
        self.initialize_database()

    def create_connection(self):
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

    def initialize_database(self):
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
        try:
            with self.create_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT SUM(amount) FROM budget WHERE entry_type = 'income'")
                income = cursor.fetchone()[0] or 0

                cursor.execute("SELECT SUM(amount) FROM budget WHERE entry_type = 'outcome'")
                outcome = cursor.fetchone()[0] or 0

                balance = income - outcome

                print(
                    f"Podsumowanie budżetu:\n - Dochody: {income:.2f} PLN\n - Wydatki: {outcome:.2f} PLN\n - Saldo: {balance:.2f} PLN")
        except sqlite3.Error as e:
            print(f"Błąd bazy danych: {e}")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")

    def delete_budget_entry(self, entry_id):
        with self.create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budget WHERE id = ?", (entry_id,))
            conn.commit()
            print(f"Wpis o ID {entry_id} został usunięty.")