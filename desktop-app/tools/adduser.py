import sqlite3
from typing import Optional, Tuple
from .category import add_default_categories_for_user

class UserError(Exception):
    """Klasa wyjątków związanych z operacjami na użytkownikach"""
    pass

def validate_user_data(username: str, email: str) -> None:
    """
    Sprawdza poprawność danych użytkownika
    
    Args:
        username: Nazwa użytkownika
        email: Adres email
    
    Raises:
        UserError: Gdy dane są niepoprawne
    """
    if not username or len(username) < 3:
        raise UserError("Nazwa użytkownika musi mieć co najmniej 3 znaki")
    
    if not email or '@' not in email or '.' not in email:
        raise UserError("Niepoprawny format adresu email")

def check_user_exists(cursor, username: str, email: str) -> bool:
    """
    Sprawdza czy użytkownik o podanej nazwie lub emailu już istnieje
    
    Returns:
        bool: True jeśli użytkownik istnieje, False w przeciwnym razie
    """
    cursor.execute('''
        SELECT username, email FROM users 
        WHERE username = ? OR email = ?
    ''', (username, email))
    
    existing = cursor.fetchone()
    if existing:
        if existing[0] == username:
            raise UserError(f"Użytkownik o nazwie '{username}' już istnieje")
        else:
            raise UserError(f"Email '{email}' jest już używany")
    return False

def create_new_user(username: str, email: str) -> Tuple[int, str]:
    """
    Tworzy nowego użytkownika i dodaje dla niego domyślne kategorie
    
    Args:
        username: Nazwa użytkownika
        email: Adres email
    
    Returns:
        Tuple[int, str]: (ID utworzonego użytkownika, nazwa użytkownika)
    
    Raises:
        UserError: Gdy wystąpi błąd podczas tworzenia użytkownika
    """
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    try:
        # Walidacja danych
        validate_user_data(username, email)
        
        # Sprawdzenie czy użytkownik już istnieje
        check_user_exists(cursor, username, email)
        
        cursor.execute("BEGIN TRANSACTION")
        
        # Dodanie użytkownika
        cursor.execute('''
            INSERT INTO users (username, email)
            VALUES (?, ?)
        ''', (username, email))
        
        user_id = cursor.lastrowid
        
        # Dodanie domyślnych kategorii
        add_default_categories_for_user(cursor, user_id)
        
        cursor.execute("COMMIT")
        print(f"Utworzono użytkownika '{username}' (ID: {user_id})")
        return user_id, username
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        if isinstance(e, UserError):
            raise
        raise UserError(f"Błąd podczas tworzenia użytkownika: {e}")
    finally:
        conn.close()

def get_user_by_username(username: str) -> Optional[Tuple[int, str, str]]:
    """
    Pobiera dane użytkownika na podstawie nazwy użytkownika
    
    Returns:
        Optional[Tuple[int, str, str]]: (user_id, username, email) lub None jeśli nie znaleziono
    """
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT user_id, username, email 
            FROM users 
            WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        return user if user else None
        
    finally:
        conn.close()

if __name__ == "__main__":
    # Przykład użycia przy uruchomieniu bezpośrednim
    try:
        username = input("Podaj nazwę użytkownika: ").strip()
        email = input("Podaj adres email: ").strip()
        
        user_id, username = create_new_user(username, email)
        print(f"\nPomyślnie utworzono użytkownika:")
        print(f"ID: {user_id}")
        print(f"Nazwa: {username}")
        print(f"Email: {email}")
        print("\nDodano domyślne kategorie przychodów i wydatków.")
        
    except UserError as e:
        print(f"\nBłąd: {e}")
    except KeyboardInterrupt:
        print("\nPrzerwano operację.")
    except Exception as e:
        print(f"\nWystąpił nieoczekiwany błąd: {e}")