import sqlite3
from datetime import datetime

def create_database():
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    # Rozpoczynamy transakcję
    cursor.execute("BEGIN TRANSACTION")
    
    try:
        # Tabela users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela currencies
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS currencies (
                currency_id VARCHAR(3) PRIMARY KEY,
                base INTEGER NOT NULL,
                exponent INTEGER NOT NULL,
                name VARCHAR(50) NOT NULL
            )
        ''')

        # Tabela accounts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number VARCHAR(26) NOT NULL UNIQUE,
                account_name VARCHAR(100) NOT NULL,
                balance DECIMAL(15,2) NOT NULL,
                user_id INTEGER NOT NULL,
                currency_id VARCHAR(3) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (currency_id) REFERENCES currencies(currency_id)
            )
        ''')

        # Tabela categories
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL,
                type VARCHAR(10) NOT NULL CHECK (type IN ('income', 'outcome')),
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Tabela transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                type VARCHAR(10) NOT NULL CHECK (type IN ('income', 'outcome')),
                description TEXT,
                transaction_date TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        ''')

        # Tworzenie indeksów
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_user ON categories(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_currency ON accounts(currency_id)')

        # Tabela migracji
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Wstawienie domyślnych walut
        cursor.execute('''
            INSERT OR IGNORE INTO currencies (currency_id, base, exponent, name) VALUES 
            ('PLN', 10, 2, 'Polski złoty'),
            ('USD', 10, 2, 'US Dollar'),
            ('EUR', 10, 2, 'Euro')
        ''')

        # Zatwierdzamy transakcję
        cursor.execute("COMMIT")
        print("Baza danych została pomyślnie utworzona!")

    except Exception as e:
        # W przypadku błędu wycofujemy zmiany
        cursor.execute("ROLLBACK")
        print(f"Błąd podczas tworzenia bazy danych: {e}")
    finally:
        conn.close()

def migrate_legacy_data():
    """Migracja danych ze starej struktury do nowej"""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    try:
        # Sprawdzamy czy istnieje stara tabela budget
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budget'")
        if cursor.fetchone():
            # TODO: Implementacja migracji starych danych
            pass
            
    except Exception as e:
        print(f"Błąd podczas migracji starych danych: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_database()
    migrate_legacy_data()