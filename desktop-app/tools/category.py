from typing import Dict, List

DEFAULT_INCOME_CATEGORIES = [
    "Wynagrodzenie",
    "Premia",
    "Zwrot podatku",
    "Odsetki bankowe",
    "Inwestycje",
    "Sprzedaż",
    "Darowizna",
    "Freelancing",
    "Wynajem",
    "Inne przychody"
]

DEFAULT_OUTCOME_CATEGORIES = [
    "Mieszkanie/Czynsz",
    "Media",
    "Żywność",
    "Transport",
    "Zdrowie",
    "Edukacja",
    "Rozrywka",
    "Ubrania",
    "Elektronika",
    "Oszczędności",
    "Ubezpieczenia",
    "Kredyty/Pożyczki",
    "Prezenty",
    "Hobby",
    "Restauracje",
    "Sport",
    "Podróże",
    "Inne wydatki"
]

def get_default_categories() -> Dict[str, List[str]]:
    """Zwraca słownik z domyślnymi kategoriami"""
    return {
        'income': DEFAULT_INCOME_CATEGORIES,
        'outcome': DEFAULT_OUTCOME_CATEGORIES
    }

def add_default_categories_for_user(cursor, user_id: int) -> None:
    """Dodaje domyślne kategorie dla nowego użytkownika"""
    try:
        # Dodawanie kategorii przychodów
        for category in DEFAULT_INCOME_CATEGORIES:
            cursor.execute('''
                INSERT INTO categories (name, type, user_id)
                VALUES (?, 'income', ?)
            ''', (category, user_id))

        # Dodawanie kategorii wydatków
        for category in DEFAULT_OUTCOME_CATEGORIES:
            cursor.execute('''
                INSERT INTO categories (name, type, user_id)
                VALUES (?, 'outcome', ?)
            ''', (category, user_id))

    except Exception as e:
        print(f"Błąd podczas dodawania domyślnych kategorii: {e}")
        raise

def add_custom_category(cursor, name: str, category_type: str, user_id: int) -> None:
    """
    Dodaje nową kategorię dla użytkownika
    
    Args:
        cursor: Cursor do bazy danych
        name: Nazwa nowej kategorii
        category_type: Typ kategorii ('income' lub 'outcome')
        user_id: ID użytkownika
    """
    if category_type not in ['income', 'outcome']:
        raise ValueError("Typ kategorii musi być 'income' lub 'outcome'")
    
    try:
        cursor.execute('''
            INSERT INTO categories (name, type, user_id)
            VALUES (?, ?, ?)
        ''', (name, category_type, user_id))
    except Exception as e:
        print(f"Błąd podczas dodawania nowej kategorii: {e}")
        raise

def get_user_categories(cursor, user_id: int, category_type: str = None) -> List[Dict]:
    """
    Pobiera kategorie użytkownika
    
    Args:
        cursor: Cursor do bazy danych
        user_id: ID użytkownika
        category_type: Opcjonalnie filtrowanie po typie ('income' lub 'outcome')
    
    Returns:
        Lista słowników z kategoriami
    """
    try:
        if category_type:
            if category_type not in ['income', 'outcome']:
                raise ValueError("Typ kategorii musi być 'income' lub 'outcome'")
            
            cursor.execute('''
                SELECT category_id, name, type
                FROM categories
                WHERE user_id = ? AND type = ?
                ORDER BY name
            ''', (user_id, category_type))
        else:
            cursor.execute('''
                SELECT category_id, name, type
                FROM categories
                WHERE user_id = ?
                ORDER BY type, name
            ''', (user_id,))
            
        categories = cursor.fetchall()
        return [
            {
                'id': category[0],
                'name': category[1],
                'type': category[2]
            }
            for category in categories
        ]
    except Exception as e:
        print(f"Błąd podczas pobierania kategorii: {e}")
        raise
