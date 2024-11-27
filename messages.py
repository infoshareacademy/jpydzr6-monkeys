# Komunikaty dotyczące hasła, żeby było bezpiecznie :)
PASSWORD_REQUIREMENTS = """
Wymagania dotyczące hasła:
• Minimum 8 znaków
• Przynajmniej jedna wielka litera (A-Z)
• Przynajmniej jedna mała litera (a-z)
• Przynajmniej jedna cyfra (0-9)
• Przynajmniej jeden znak specjalny (!@#$%^&*()_+-=[]{}|;:,.<>?)

Przykład dobrego hasła: 'Admin@2024!'
"""

# Komunikaty błędów hasła
PASSWORD_TOO_SHORT = f"""
❌ Hasło jest za krótkie! 
{PASSWORD_REQUIREMENTS}"""

PASSWORD_NO_UPPERCASE = f"""
❌ Brak wielkiej litery! 
{PASSWORD_REQUIREMENTS}"""

PASSWORD_NO_LOWERCASE = f"""
❌ Brak małej litery! 
{PASSWORD_REQUIREMENTS}"""

PASSWORD_NO_DIGIT = f"""
❌ Brak cyfry! 
{PASSWORD_REQUIREMENTS}"""

PASSWORD_NO_SPECIAL = f"""
❌ Brak znaku specjalnego! 
{PASSWORD_REQUIREMENTS}"""

PASSWORD_OK = "✅ Hasło spełnia wszystkie wymagania!"

# Komunikaty dotyczące emaila
EMAIL_INVALID = "❌ Nieprawidłowy format emaila"
EMAIL_TOO_SHORT = "❌ Email jest za krótki"
EMAIL_NO_DOMAIN = "❌ Nieprawidłowa domena"
EMAIL_OK = "✅ Email jest poprawny"

# Menu i inne komunikaty używane przy pliku test_user_manager.py
MAIN_MENU = """
1. Dodaj użytkownika
2. Usuń użytkownika
3. Edytuj użytkownika
4. Pokaż użytkowników
5. Zaloguj się
0. Wyjście
""" 