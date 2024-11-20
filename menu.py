from abc import ABC, abstractmethod
from account.account import AccountManager


class MenuItem(ABC):

    @property
    @abstractmethod
    def name(self):  # dodanie nazwy submenu, która będzie wyświetlona  menu głównym
        pass

    @property
    @abstractmethod
    def letter(self): # dodanie litery, pod którą dane submenu będzie dostępne
        pass

    @property
    @abstractmethod
    def submenu_name(self): # dodanie nazwy submenu, która będzie wyświetlona razem z submenu
        pass

    @abstractmethod
    def get_submenu_items(self) -> dict[str,str]: # przygotowuje słownik opcji dostępnych z submenu
        pass                                      # w formacie {'litera': 'nazwa opcji widziana w menu'}

    @abstractmethod
    def do_action(self, choice: str): # miejsce wywoływana konkretnych metod dostępnych z submenu
        pass


class AccountHandling(MenuItem):

    @property
    def name(self):
        return 'Zarządzanie kontami bankowymi'

    @property
    def letter(self):
        return 'K'

    @property
    def submenu_name(self):
        return 'Menu obsługi kont bankowych'

    def get_submenu_items(self) -> dict[str,str]:
        return {'D': 'Dodaj konto'}

    def do_action(self, choice: str) -> None:
        account_manager = AccountManager()
        match choice:
            case 'D':
                while True:
                    account_number = input('Podaj numer konta: ')
                    if len(account_number) != 26:
                        print('Numer konta skłąda się z 26 cyfr.')
                        continue
                    try:
                        account_number_test = int(account_number)
                    except ValueError:
                        print('Numer konta powinien składać się z liczb.')
                        continue
                    break
                while True:
                    try:
                        balance = float(input('Podaj aktualny stan konta: '))
                    except ValueError:
                        print('Stan konta powinien być podany za pomocą liczb.')
                        continue
                    break
                while True:
                    try: #todo konieczne sprawdzenia istnienia użytkownika w bazie danych
                        user_id = int(input('Podaj ID właściciela konta: '))
                    except ValueError:
                        print('Podane nieprawidłowe ID.')
                        continue
                    break
                while True:
                    currency = input('Podaj w jaką walutę obsługuje konto: ').upper()
                    if currency not in ['PLN', 'USD', 'EUR']:
                        print('Podano nieprawidłową walutę.')
                        continue
                    break
                account_name = input('Nadaj kontu nazwę: ')

                account_manager.add_account(
                    account_number=account_number,
                    account_name=account_name,
                    balance=balance,
                    user_id=user_id,
                    currency=currency
                )

if __name__ == '__main__':
    pass
