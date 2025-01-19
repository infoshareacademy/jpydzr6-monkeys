from reports.reports import FinancialReports
from datetime import datetime
import calendar
import sqlite3
from typing import List, Tuple

def get_user_input(prompt: str, valid_options: list) -> str:
    """Pobiera i waliduje dane wejściowe od użytkownika"""
    while True:
        choice = input(prompt).strip().upper()
        if choice in valid_options:
            return choice
        print(f"Nieprawidłowy wybór. Dostępne opcje: {', '.join(valid_options)}")

def get_date_input() -> tuple:
    """Pobiera rok i miesiąc od użytkownika"""
    current_year = datetime.now().year
    while True:
        try:
            year = int(input(f"Podaj rok (2020-{current_year}): "))
            if 2020 <= year <= current_year:
                break
            print(f"Rok musi być między 2020 a {current_year}")
        except ValueError:
            print("Nieprawidłowy format roku")
    
    while True:
        try:
            month = int(input("Podaj miesiąc (1-12): "))
            if 1 <= month <= 12:
                break
            print("Miesiąc musi być między 1 a 12")
        except ValueError:
            print("Nieprawidłowy format miesiąca")
    
    return year, month

def print_monthly_summary(reports: FinancialReports):
    """Wyświetla miesięczne podsumowanie"""
    year, month = get_date_input()
    summary = reports.monthly_summary(year, month)
    
    print(f"\nPodsumowanie za {summary['period']}:")
    print(f"Przychody: {summary['income']['total']:.2f}")
    print(f"Wydatki: {summary['outcome']['total']:.2f}")
    print(f"Bilans: {summary['balance']:.2f}")
    
    print("\nTop kategorie wydatków:")
    for category in summary['outcome']['by_category'][:5]:
        print(f"- {category['category']}: {category['amount']:.2f}")
    
    print("\nTop kategorie przychodów:")
    for category in summary['income']['by_category'][:3]:
        print(f"- {category['category']}: {category['amount']:.2f}")

def print_savings_analysis(reports: FinancialReports):
    """Wyświetla analizę oszczędności"""
    savings = reports.savings_analysis()
    
    print("\nAnaliza oszczędności:")
    print(f"Całkowite oszczędności: {savings['total_savings']:.2f}")
    print(f"Średnie miesięczne oszczędności: {savings['average_monthly_saving']:.2f}")
    
    if savings['best_month']:
        print(f"Najlepszy miesiąc: {savings['best_month']['month']} "
              f"(+{savings['best_month']['amount']:.2f})")
    
    if savings['worst_month']:
        print(f"Najgorszy miesiąc: {savings['worst_month']['month']} "
              f"({savings['worst_month']['amount']:.2f})")

def print_recommendations(reports: FinancialReports):
    """Wyświetla rekomendacje budżetowe"""
    recommendations = reports.budget_recommendations()
    
    print("\nRekomendacje budżetowe:")
    for category in recommendations['high_spending_categories']:
        print(f"\n{category['recommendation']}")
        print(f"- Obecne wydatki: {category['total']:.2f} "
              f"({category['percentage']:.1f}% wszystkich wydatków)")
        print(f"- Średnia transakcja: {category['average_transaction']:.2f}")
    
    print("\nPotencjalne oszczędności:")
    for saving in recommendations['potential_savings']:
        print(f"\n{saving['category']}:")
        print(f"- {saving['suggestion']}")
        print(f"- Możliwe miesięczne oszczędności: {saving['potential_monthly_saving']:.2f}")

def print_spending_trends(reports: FinancialReports):
    """Wyświetla trendy wydatków"""
    months = int(input("Za ile ostatnich miesięcy pokazać trendy? (1-12): "))
    trends = reports.spending_trends(months)
    
    print("\nTrendy wydatków:")
    for trend in trends:
        print(f"\nMiesiąc: {trend['month']}")
        print(f"Całkowite przychody: {trend['total_income']:.2f}")
        print(f"Całkowite wydatki: {trend['total_outcome']:.2f}")
        print("Top 3 kategorie wydatków:")
        for category in trend['outcome'][:3]:
            print(f"- {category['category']}: {category['amount']:.2f}")

def print_available_periods(reports: FinancialReports):
    """Wyświetla dostępne okresy dla raportów"""
    try:
        # Pobieranie zakresu dat z transakcji
        reports.cursor.execute("""
            SELECT 
                MIN(strftime('%Y-%m', transaction_date)) as first_month,
                MAX(strftime('%Y-%m', transaction_date)) as last_month,
                COUNT(DISTINCT strftime('%Y-%m', transaction_date)) as total_months,
                COUNT(*) as total_transactions
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ?
        """, (reports.user_id,))
        
        result = reports.cursor.fetchone()
        first_month, last_month, total_months, total_transactions = result
        
        if not first_month:
            print("\nBrak transakcji w bazie danych.")
            return
        
        # Pobieranie szczegółów dla każdego roku
        reports.cursor.execute("""
            SELECT 
                strftime('%Y', transaction_date) as year,
                COUNT(DISTINCT strftime('%m', transaction_date)) as months_with_data,
                COUNT(*) as transactions,
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'outcome' THEN amount ELSE 0 END) as total_outcome
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ?
            GROUP BY year
            ORDER BY year
        """, (reports.user_id,))
        
        yearly_stats = reports.cursor.fetchall()
        
        # Wyświetlanie podsumowania
        print("\n=== DOSTĘPNE OKRESY DLA RAPORTÓW ===")
        print(f"\nZakres dat: {first_month} - {last_month}")
        print(f"Łączna liczba miesięcy z danymi: {total_months}")
        print(f"Łączna liczba transakcji: {total_transactions}")
        
        # Wyświetlanie statystyk rocznych
        print("\nStatystyki roczne:")
        print("-" * 80)
        print(f"{'Rok':<10} {'Miesięcy z danymi':<20} {'Transakcji':<15} {'Przychody':<15} {'Wydatki':<15}")
        print("-" * 80)
        
        for year, months, trans, income, outcome in yearly_stats:
            print(f"{year:<10} {months:^20} {trans:^15} {income:>15.2f} {outcome:>15.2f}")
        
        # Pobieranie szczegółów miesięcznych dla ostatniego roku
        last_year = yearly_stats[-1][0]
        reports.cursor.execute("""
            SELECT 
                strftime('%m', transaction_date) as month,
                COUNT(*) as transactions,
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type = 'outcome' THEN amount ELSE 0 END) as outcome
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ?
            AND strftime('%Y', transaction_date) = ?
            GROUP BY month
            ORDER BY month
        """, (reports.user_id, last_year))
        
        monthly_stats = reports.cursor.fetchall()
        
        # Wyświetlanie statystyk miesięcznych dla ostatniego roku
        print(f"\nSzczegóły miesięczne dla roku {last_year}:")
        print("-" * 65)
        print(f"{'Miesiąc':<10} {'Transakcji':<15} {'Przychody':<15} {'Wydatki':<15}")
        print("-" * 65)
        
        for month, trans, income, outcome in monthly_stats:
            month_name = calendar.month_name[int(month)]
            print(f"{month_name:<10} {trans:^15} {income:>15.2f} {outcome:>15.2f}")
            
    except Exception as e:
        print(f"\nBłąd podczas pobierania dostępnych okresów: {e}")

def get_available_users(cursor) -> List[Tuple[int, str, str]]:
    """Pobiera listę dostępnych użytkowników"""
    cursor.execute("""
        SELECT user_id, username, email 
        FROM users 
        ORDER BY username
    """)
    return cursor.fetchall()

def select_user() -> int:
    """Pozwala użytkownikowi wybrać konto do analizy"""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    try:
        users = get_available_users(cursor)
        if not users:
            print("Brak użytkowników w bazie danych!")
            return None
        
        print("\n=== DOSTĘPNI UŻYTKOWNICY ===")
        print("-" * 60)
        print(f"{'ID':<5} {'Nazwa użytkownika':<20} {'Email':<30}")
        print("-" * 60)
        
        for user_id, username, email in users:
            print(f"{user_id:<5} {username:<20} {email:<30}")
        
        while True:
            try:
                user_id = input("\nWybierz ID użytkownika lub 'Q' aby wyjść: ").strip()
                if user_id.upper() == 'Q':
                    return None
                
                user_id = int(user_id)
                if user_id in [u[0] for u in users]:
                    return user_id
                print("Nieprawidłowe ID użytkownika")
            except ValueError:
                print("ID użytkownika musi być liczbą")
    finally:
        conn.close()

def main_menu():
    """Główne menu programu"""
    user_id = select_user()
    if not user_id:
        print("Program zakończony.")
        return
    
    menu_options = {
        '1': ('Miesięczne podsumowanie', print_monthly_summary),
        '2': ('Analiza oszczędności', print_savings_analysis),
        '3': ('Rekomendacje budżetowe', print_recommendations),
        '4': ('Trendy wydatków', print_spending_trends),
        '5': ('Dostępne okresy raportowania', print_available_periods),
        'U': ('Zmień użytkownika', None),
        'Q': ('Wyjście', None)
    }
    
    with FinancialReports(user_id) as reports:
        while True:
            username = get_available_users(reports.cursor)[0][1]  # Pobieranie nazwy aktualnego użytkownika
            print(f"\n=== RAPORTY FINANSOWE (Użytkownik: {username}) ===")
            for key, (name, _) in menu_options.items():
                print(f"{key}. {name}")
            
            choice = get_user_input(
                "\nWybierz opcję: ",
                list(menu_options.keys())
            )
            
            if choice == 'Q':
                print("Do widzenia!")
                break
            
            if choice == 'U':
                new_user_id = select_user()
                if new_user_id:
                    user_id = new_user_id
                    reports = FinancialReports(user_id)
                continue
            
            try:
                menu_options[choice][1](reports)
                input("\nNaciśnij Enter, aby kontynuować...")
            except Exception as e:
                print(f"Wystąpił błąd: {e}")
                input("\nNaciśnij Enter, aby kontynuować...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nProgram zakończony przez użytkownika.")
    except Exception as e:
        print(f"\nWystąpił nieoczekiwany błąd: {e}") 