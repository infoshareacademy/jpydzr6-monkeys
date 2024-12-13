# python3 -m tools.sample_data
import sqlite3
from datetime import datetime, timedelta
import random
from typing import List, Dict
from decimal import Decimal
import string
from .category import add_default_categories_for_user

# Przykładowe dane
SAMPLE_USERS = [
    ("jan_kowalski", "jan.kowalski@example.com"),
    ("anna_nowak", "anna.nowak@example.com"),
    ("piotr_wisniewski", "piotr.wisniewski@example.com"),
    ("maria_dabrowska", "maria.dabrowska@example.com"),
    ("tomasz_lewandowski", "tomasz.l@example.com")
]

SAMPLE_ACCOUNTS = [
    # (nazwa, początkowe saldo, waluta)
    ("Konto główne", 3500, "PLN"),
    ("Oszczędności", 8000, "PLN"),
    ("Konto USD", 500, "USD"),
    ("Konto EUR", 400, "EUR"),
    ("Konto emerytalne", 12000, "PLN")
]

def generate_account_number() -> str:
    """Generuje losowy 26-cyfrowy numer konta"""
    country = "PL"
    check_digits = str(random.randint(10, 99))
    bank_code = "109010140"  # przykładowy kod banku
    account = ''.join(random.choices(string.digits, k=16))
    return f"{country}{check_digits}{bank_code}{account}"

def generate_transaction_description(category_name: str) -> str:
    """Generuje opis transakcji na podstawie kategorii"""
    descriptions = {
        "Wynagrodzenie": ["Wypłata", "Premia kwartalna", "Nadgodziny", "Dodatek funkcyjny"],
        "Premia": ["Premia świąteczna", "Premia roczna", "Bonus za wyniki"],
        "Zwrot podatku": ["Zwrot PIT", "Zwrot VAT"],
        "Odsetki bankowe": ["Odsetki z lokaty", "Kapitalizacja odsetek"],
        "Inwestycje": ["Dywidenda", "Zysk ze sprzedaży akcji", "Zwrot z obligacji"],
        "Sprzedaż": ["Sprzedaż na Allegro", "Sprzedaż samochodu", "Sprzedaż sprzętu"],
        "Darowizna": ["Darowizna rodzinna", "Spadek"],
        "Freelancing": ["Projekt IT", "Tłumaczenie", "Konsultacje"],
        "Wynajem": ["Czynsz za mieszkanie", "Wynajem garażu"],
        "Mieszkanie/Czynsz": ["Czynsz miesięczny", "Opłata za mieszkanie"],
        "Media": ["Prąd", "Gaz", "Woda", "Internet"],
        "Żywność": ["Zakupy spożywcze", "Biedronka", "Lidl", "Kaufland"],
        "Transport": ["Paliwo", "Bilet miesięczny", "Uber", "Bolt"],
        "Zdrowie": ["Wizyta lekarska", "Leki", "Badania"],
        "Edukacja": ["Kurs online", "Książki", "Szkolenie"],
        "Rozrywka": ["Kino", "Netflix", "Spotify", "Koncert"],
        "Ubrania": ["H&M", "Zara", "Reserved", "CCC"],
        "Elektronika": ["RTV Euro AGD", "Media Expert", "Akcesoria"],
        "Oszczędności": ["Wpłata na lokatę", "Fundusz inwestycyjny"],
        "Ubezpieczenia": ["OC/AC", "Ubezpieczenie na życie", "Ubezpieczenie mieszkania"],
        "Kredyty/Pożyczki": ["Rata kredytu", "Spłata pożyczki"],
        "Prezenty": ["Urodziny", "Święta", "Rocznica"],
        "Hobby": ["Sprzęt sportowy", "Książki", "Gry"],
        "Restauracje": ["McDonald's", "Restauracja włoska", "Sushi"],
        "Sport": ["Karnet na siłownię", "Basen", "Sprzęt sportowy"],
        "Podróże": ["Lot", "Hotel", "Wycieczka"]
    }
    
    return random.choice(descriptions.get(category_name, ["Transakcja"]))

def generate_transaction_amount(category_name: str, trans_type: str) -> float:
    """Generuje realistyczną kwotę transakcji na podstawie kategorii"""
    if trans_type == 'income':
        ranges = {
            "Wynagrodzenie": (3000, 6000),
            "Premia": (500, 2000),
            "Zwrot podatku": (400, 1200),
            "Odsetki bankowe": (10, 100),
            "Inwestycje": (100, 1000),
            "Sprzedaż": (50, 500),
            "Darowizna": (100, 1000),  # rzadkie wydarzenie
            "Freelancing": (200, 2000),
            "Wynajem": (1500, 2500),
            "Inne przychody": (50, 500)
        }
    else:
        ranges = {
            "Mieszkanie/Czynsz": (1200, 2000),
            "Media": (200, 600),
            "Żywność": (200, 800),
            "Transport": (100, 300),
            "Zdrowie": (50, 400),
            "Edukacja": (100, 500),
            "Rozrywka": (50, 200),
            "Ubrania": (100, 500),
            "Elektronika": (200, 2000),  # rzadkie zakupy
            "Oszczędności": (200, 1000),
            "Ubezpieczenia": (100, 300),
            "Kredyty/Pożyczki": (500, 1500),
            "Prezenty": (50, 300),
            "Hobby": (50, 300),
            "Restauracje": (50, 200),
            "Sport": (50, 200),
            "Podróże": (200, 2000),  # rzadkie wydarzenia
            "Inne wydatki": (20, 200)
        }
    
    default_range = (50, 500)
    min_amount, max_amount = ranges.get(category_name, default_range)
    return round(random.uniform(min_amount, max_amount), 2)

def should_generate_transaction(category_name: str) -> bool:
    """Określa czy generować transakcję na podstawie typu kategorii"""
    rare_categories = {
        "Darowizna": 0.05,  # 5% szans na wystąpienie
        "Elektronika": 0.1,
        "Podróże": 0.15,
        "Zwrot podatku": 0.08,
        "Premia": 0.2
    }
    
    if category_name in rare_categories:
        return random.random() < rare_categories[category_name]
    return True

def create_sample_data():
    """Tworzy przykładowe dane w bazie"""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN TRANSACTION")
        
        # Dodawanie użytkowników
        for username, email in SAMPLE_USERS:
            cursor.execute('''
                INSERT INTO users (username, email)
                VALUES (?, ?)
            ''', (username, email))
            
            user_id = cursor.lastrowid
            
            # Dodawanie kategorii dla użytkownika
            add_default_categories_for_user(cursor, user_id)
            
            # Dodawanie kont dla każdego użytkownika
            for acc_name, balance, currency in SAMPLE_ACCOUNTS:
                account_number = generate_account_number()
                cursor.execute('''
                    INSERT INTO accounts (account_number, account_name, balance, user_id, currency_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (account_number, acc_name, balance, user_id, currency))
                
                account_id = cursor.lastrowid
                
                # Pobieranie kategorii dla użytkownika
                cursor.execute('SELECT category_id, name, type FROM categories WHERE user_id = ?', (user_id,))
                categories = cursor.fetchall()
                
                if not categories:
                    raise Exception(f"Brak kategorii dla użytkownika {username}")
                
                # Generowanie transakcji dla ostatnich 12 miesięcy
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                current_date = start_date
                
                # Zmniejszamy liczbę transakcji dla przyspieszenia generowania danych
                days_with_transactions = random.sample(range(365), 120)  # 120 dni z transakcjami
                
                for day in range(365):
                    if day not in days_with_transactions:
                        current_date += timedelta(days=1)
                        continue
                        
                    # 1-3 transakcje w dniach z aktywnością
                    for _ in range(random.randint(1, 3)):
                        category = random.choice(categories)
                        category_id, category_name, trans_type = category
                        
                        if not should_generate_transaction(category_name):
                            continue
                        
                        amount = generate_transaction_amount(category_name, trans_type)
                        
                        # Dodajemy losową godzinę do transakcji
                        transaction_time = current_date.replace(
                            hour=random.randint(8, 20),
                            minute=random.randint(0, 59),
                            second=random.randint(0, 59)
                        )
                        
                        description = generate_transaction_description(category_name)
                        
                        cursor.execute('''
                            INSERT INTO transactions 
                            (account_id, category_id, amount, type, description, transaction_date)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (account_id, category_id, amount, trans_type, 
                              description, transaction_time.strftime('%Y-%m-%d %H:%M:%S')))
                    
                    current_date += timedelta(days=1)
        
        cursor.execute("COMMIT")
        print("Pomyślnie dodano przykładowe dane do bazy!")
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"Błąd podczas dodawania przykładowych danych: {e}")
        raise  # Dodajemy raise, aby zobaczyć pełny traceback
    finally:
        conn.close()

def count_records():
    """Wyświetla liczbę rekordów w każdej tabeli"""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    tables = ['users', 'accounts', 'categories', 'transactions']
    
    print("\nLiczba rekordów w tabelach:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count}")
        
        # Dodatkowe informacje dla transakcji
        if table == 'transactions':
            cursor.execute("""
                SELECT type, COUNT(*), ROUND(AVG(amount), 2)
                FROM transactions
                GROUP BY type
            """)
            for trans_type, count, avg_amount in cursor.fetchall():
                print(f"  - {trans_type}: {count} transakcji, średnia kwota: {avg_amount}")
    
    conn.close()

if __name__ == "__main__":
    try:
        create_sample_data()
        count_records()
    except KeyboardInterrupt:
        print("\nPrzerwano generowanie danych.")
    except Exception as e:
        print(f"\nWystąpił nieoczekiwany błąd: {e}") 