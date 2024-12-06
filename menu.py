from abc import ABC, abstractmethod
from account.account import AccountManager, SQLError, ACCOUNT_PARAMETERS
from helper import Helper, InvalidData
from money import currency, monetary


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
        return {'D': 'Dodaj konto', 'E':'Edytuj konto', 'U': 'Usuń konto', 'P': 'Pokaż szczegóły konta'}


    def do_action(self, choice: str) -> None:
        account_manager = AccountManager()
        validation = Helper()
        match choice:
            case 'D': # todo zmodyfikuj do klas Marka
                while True:
                    # todo daj możliwość dodawania gotówki (numer konta ma być unikalny, ale tylko, jeśli istnieje)
                    # todo popraw walidację istnienia konta, żeby była od razu
                    account_number = input('Podaj numer konta: ')
                    try: #todo trzeba ustawić odpowiednią długośc numeru konta
                        validation.check_length(account_number,4,'Nieprawidłowa długość numeru konta')
                        validation.check_value(account_number, int,'Numer konta powinien składać się z liczb')
                    except InvalidData as e:
                        print(f'\nNieprawidłowe dane: {e}')
                        continue
                    break
                while True:
                    balance = input('Podaj aktualny stan konta: ')
                    try:
                        balance = validation.check_value(balance, float, 'Stan konta powinien być podany jako liczba.')
                    except InvalidData as e:
                        print(f'\nNieprawidłowe dane: {e}')
                        continue
                    break

                while True:
                    currency = input('Podaj w jaką walutę obsługuje konto: ').upper()
                    if currency.upper() not in ['PLN', 'USD', 'EUR']: # todo zaciągniemy od Marka
                        print('\nPodano nieprawidłową walutę.')
                        continue
                    break
                account_name = input('Nadaj kontu nazwę: ')

                account_manager.add_account(
                    account_number=account_number,
                    account_name=account_name,
                    balance=balance,
                    currency_id=currency
                )
            case 'U':
                account_id = input('Podaj numer ID konta do usunięcia: ')
                try:
                    account_manager.delete_account(account_id=account_id)
                except SQLError as e:
                    print(f'Wystąpił błąd: {e}')

            case 'E': # todo dotaj tu jeszcze wyświetlenie aktualnej wartości
                try:
                    account_manager.show_account('')
                except SQLError as e:
                    print(f'\nWystąpił błąd: {e}')
                while True:
                    try: # todo walidacja account_id do inta
                        account_id = input('Podaj ID konta, które chcesz edytować lub porzuć edycję [Q]: ')
                        if account_id.upper() == 'Q':
                            return None
                        account_id = validation.check_value(account_id, int, 'Numer konta powinien być liczbą.')
                    except InvalidData as e:
                        print(f'\nWystąpił błąd: {e}')
                        continue
                    try:
                        AccountManager().check_record_existence(account_id=account_id)
                    except SQLError as e:
                        print(f'\nWystąpił błąd: {e}')
                        continue
                    break

                print('Możliwe do zmiany parametry konta:')
                print('1 - numer konta\n'
                      '2 - nazwa konta\n'
                      '3 - stan konta\n'
                      '4 - waluta\n'
                      'Q - porzuć edycję')

                while True:
                    param_to_change_from_user = input('Podaj jaki parametr konta chcesz zmienić: ')
                    if param_to_change_from_user.upper() == 'Q':
                        return None
                    try:
                        parameter_to_change = ACCOUNT_PARAMETERS[param_to_change_from_user]
                    except KeyError:
                        print('\nNieprawidłowy wybór.')
                        continue
                    break
                while True:
                    new_value = input('Podaj nową wartość: ')
                    match param_to_change_from_user:
                        case '1':
                            try:
                                validation.check_value(new_value, int, 'podana wartość powinna być liczbą całkowitą.')
                            except InvalidData as e:
                                print(f'\nWystąpił błąd: {e}')
                                continue
                            break
                        case '3':
                            try:
                                validation.check_value(new_value, float,'podana wartość powinna być liczbą.')
                            except InvalidData as e:
                                print(f'\nWystąpił błąd: {e}')
                                continue
                            break
                        case '4':
                            if new_value.upper() not in ['PLN', 'USD', 'EUR']: # todo zaciągniemy od Marka
                                print('\nPodano nieprawidłową walutę.')
                                continue
                            break
                    break
                try:
                    account_manager.edit_account(account_id, parameter_to_change, new_value)
                except SQLError as e:
                    print(f'\nWystąpił błąd: {e}')
                print('Zmiana została wykonana.')
            case 'P': # todo walidacja account_id do inta
                account_id = input('Podaj numer id konta, którego szczegóły chcesz wyświetlić lub wciśnij enter, żeby zobaczyć wszystkie konta.')
                try:
                    account_manager.show_account(account_id)
                except SQLError as e:
                    print(f'\nWystąpił błąd: {e}')
