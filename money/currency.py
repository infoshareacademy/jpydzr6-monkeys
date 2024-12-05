import requests
import sqlite3

class Currency:
    def __init__(self, database):
        """
        Inicjalizuje obiekt klasy Currency.
        :param database: Ścieżka do pliku bazy danych SQLite
        """
        self.database = database

    def get_rate_from_api(self, currency):
        """
        Pobiera dane kursu waluty z API NBP.
        :param currency: Kod waluty (np. 'USD', 'EUR')
        :return: Słownik z danymi kursu waluty
        """
        url = f"https://api.nbp.pl/api/exchangerates/rates/A/{currency}/?format=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                'currency': currency,
                'currency_name': data['currency'],
                'currency_date': data['rates'][0]['effectiveDate'],
                'actual_value': data['rates'][0]['mid']
            }
        else:
            raise ValueError(f"Błąd podczas pobierania danych z API: {response.status_code}")

    def save_rate_to_db(self, rate_data, table_name):
        """
        Zapisuje dane kursu waluty do bazy danych SQLite.
        :param rate_data: Słownik z danymi kursu waluty
        :param table_name: Nazwa tabeli, do której dane mają być zapisane
        """
        with sqlite3.connect(self.database) as conn:
            cursor = conn.cursor()

            # Tworzenie tabeli, jeśli nie istnieje
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency TEXT,
                    currency_name TEXT,
                    currency_date TEXT,
                    actual_value REAL
                )
            """)

            # Wstawianie danych
            cursor.execute(f"""
                INSERT INTO {table_name} (currency, currency_name, currency_date, actual_value)
                VALUES (?, ?, ?, ?)
            """, (rate_data['currency'], rate_data['currency_name'], rate_data['currency_date'], rate_data['actual_value']))

    def get_and_save(self, currency, table_name):
        """
        Pobiera dane kursu waluty z API i zapisuje je do bazy danych.
        :param currency: Kod waluty (np. 'USD', 'EUR')
        :param table_name: Nazwa tabeli, do której dane mają być zapisane
        """
        try:
            rate_data = self.get_rate_from_api(currency)
            self.save_rate_to_db(rate_data, table_name)
            print(f"Kurs {currency} z dnia {rate_data['currency_date']} zapisany do tabeli {table_name}.")
        except Exception as e:
            print(f"Wystąpił błąd: {e}")


# Przykład użycia klasy
## if __name__ == "__main__":
##    fetcher = Currency("database.db")
##    fetcher.get_and_save("USD", "currency_table")
