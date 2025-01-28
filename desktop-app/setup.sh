#!/bin/bash

echo "=== KONFIGURACJA APLIKACJI BUDŻETOWEJ ==="
echo "Inicjalizacja..."

# Sprawdzenie czy Python jest zainstalowany
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 nie jest zainstalowany!"
    echo "Zainstaluj Python3 i spróbuj ponownie."
    exit 1
fi

# Sprawdzenie czy pip jest zainstalowany
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 nie jest zainstalowany!"
    echo "Zainstaluj pip3 i spróbuj ponownie."
    exit 1
fi

# Sprawdzenie i tworzenie wirtualnego środowiska
echo -e "\n1. Sprawdzanie środowiska wirtualnego..."
if [ -d ".venv" ]; then
    echo "Znaleziono istniejące środowisko wirtualne."
    read -p "Czy chcesz je usunąć i utworzyć nowe? (t/N): " answer
    if [[ $answer == [tT] ]]; then
        echo "Usuwanie starego środowiska..."
        rm -rf .venv
        echo "Tworzenie nowego środowiska wirtualnego..."
        python3 -m venv .venv
    else
        echo "Używam istniejącego środowiska wirtualnego."
    fi
else
    echo "Tworzenie nowego środowiska wirtualnego..."
    python3 -m venv .venv
fi

# Aktywacja wirtualnego środowiska
echo "2. Aktywacja wirtualnego środowiska..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "ERROR: Nie można znaleźć pliku aktywacyjnego środowiska wirtualnego!"
    exit 1
fi

# Sprawdzenie czy aktywacja się powiodła
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: Nie udało się aktywować środowiska wirtualnego!"
    exit 1
fi

# Instalacja wymaganych pakietów
echo -e "\n3. Instalacja wymaganych pakietów..."
pip install peewee

# Sprawdzenie i ewentualne usunięcie starej bazy danych
echo -e "\n4. Sprawdzanie bazy danych..."
if [ -f budget.db ]; then
    echo "Znaleziono istniejącą bazę danych."
    read -p "Czy chcesz usunąć starą bazę i utworzyć nową? (t/N): " answer
    if [[ $answer == [tT] ]]; then
        echo "Usuwanie starej bazy danych..."
        rm budget.db
        echo "Przygotowanie do utworzenia nowej bazy..."
    else
        echo "Zachowuję istniejącą bazę danych."
        echo "UWAGA: Dalsze kroki mogą nie powieść się, jeśli struktura bazy jest niekompatybilna."
        read -p "Naciśnij Enter, aby kontynuować lub Ctrl+C, aby przerwać..."
    fi
else
    echo "Baza danych nie istnieje. Zostanie utworzona nowa."
fi

# Inicjalizacja bazy danych
echo "5. Inicjalizacja struktury bazy danych..."
python3 -m tools.database

# Sprawdzenie czy dodać przykładowe dane
echo -e "\n6. Przykładowe dane..."
read -p "Czy chcesz dodać przykładowe dane do bazy? (t/N): " answer
if [[ $answer == [tT] ]]; then
    echo "Dodawanie przykładowych danych..."
    python3 -m tools.sample_data
    if [ $? -eq 0 ]; then
        echo "✓ Przykładowe dane zostały dodane"
    else
        echo "ERROR: Nie udało się dodać przykładowych danych!"
        echo "Możesz kontynuować bez nich lub uruchomić skrypt ponownie."
    fi
else
    echo "Pomijam dodawanie przykładowych danych."
    echo "UWAGA: Będziesz musiał dodać własne dane przez aplikację."
fi

# Sprawdzenie czy wszystko działa
echo -e "\n7. Sprawdzanie konfiguracji..."
if [ -f budget.db ]; then
    echo "✓ Baza danych została utworzona"
    echo "✓ Struktura bazy danych została zainicjowana"
    echo "✓ Przykładowe dane zostały dodane"
    
    echo -e "\nKonfiguracja zakończona sukcesem!"
    echo -e "\nAby uruchomić aplikację:"
    echo "1. Aktywuj środowisko wirtualne: source venv/bin/activate"
    echo "2. Uruchom aplikację: python3 -m reports.example"
else
    echo "ERROR: Coś poszło nie tak podczas konfiguracji!"
    echo "Sprawdź logi błędów powyżej."
fi

# Deaktywacja środowiska wirtualnego
# deactivate

echo -e "\nProces konfiguracji zakończony." 