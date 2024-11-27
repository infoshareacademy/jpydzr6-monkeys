from abc import ABC, abstractmethod
from account.account import AccountManager
from helper import Helper, InvalidData


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
                validation = Helper()
                while True:
                    account_number = input('Podaj numer konta: ')
                    try:
                        validation.check_length(account_number,4,'Nieprawidłowa długość numeru konta')
                        validation.check_value(account_number, int,'Numer konta powinien składać się z liczb')
                    except InvalidData as e:
                        print(f'Nieprawidłowe dane: {e}')
                        continue
                    break
                while True:
                    balance = input('Podaj aktualny stan konta: ')
                    try:
                        balance = validation.check_value(balance, float, 'Stan konta powinien być podany jako liczba.')
                    except InvalidData as e:
                        print(f'Nieprawidłowe dane: {e}')
                        continue
                    break
                while True:
#todo konieczne sprawdzenia istnienia użytkownika w bazie danych
                    user_id = input('Podaj ID właściciela konta: ')
                    try:
                        user_id = validation.check_value(user_id, int, 'Podano nieprawidłowe ID')
                    except InvalidData as e:
                        print(f'Nieprawidłowe dane: {e}')
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
                    currency_id=currency
                )

if __name__ == '__main__':
    pass
