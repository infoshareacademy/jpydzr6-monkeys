from abc import ABC, abstractmethod
from account.account import AccountManager, SQLError, ACCOUNT_PARAMETERS
from helper import Helper, InvalidData

class MenuItem(ABC):

    @property
    @abstractmethod
    def name(self):  # dodanie nazwy submenu, która będzie wyświetlona menu głównym
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
            case 'D':
                while True:
                    account_number_choice = input('Czy chcesz podać numer konta? T/N').upper()
                    if account_number_choice not in ('T', 'N'):
                        print('\nNieprawidłowy wybór.')
                        continue
                    break
                while True:
                    if account_number_choice == 'N':
                        account_number = None
                        break
                    account_number = input('Podaj numer konta: ')
                    try:
                        validation.check_value(account_number, int,'Numer konta powinien składać się z liczb')
                        account_manager.check_account_number_existence(account_number)
                    except InvalidData as e:
                        print(f'\nNieprawidłowe dane: {e}')
                        continue
                    except SQLError as e:
                        print(f'Wystąpił błąd: {e}')
                        continue
                    break
                while True:
                    balance = input('Podaj aktualny stan konta: ')
                    try:
                        balance = validation.check_value(balance, float, 'Stan konta powinien być podany jako liczba z kropką jako separatorem.')
                    except InvalidData as e:
                        print(f'\nNieprawidłowe dane: {e}')
                        continue
                    break

                while True:
                    currency_id = input('Podaj w jaką walutę obsługuje konto: ').upper()
                    try:
                        validation.check_currency(currency_id, 'Podano nieprawidłową walutę.')
                    except InvalidData as e:
                        print(f'Wystąpił błąd: {e}')
                        continue
                    break

                account_name = input('Nadaj kontu nazwę: ')
                try:
                    account_manager.add_account(
                        account_number=account_number,
                        account_name=account_name,
                        balance=balance,
                        currency_id=currency_id
                    )
                except SQLError as e:
                    print(f'Wystąpił błąd: {e}')

            case 'U':
                try:
                    account_manager.show_account('')
                except SQLError as e:
                    print(f'\nWystąpił błąd: {e}')
                while True:
                    account_id = input('Podaj numer ID konta do usunięcia: ')
                    try:
                        account_id_int = validation.check_value(account_id, int, 'Numer ID konta powinien być liczbą.')
                        account_manager.check_record_existence(account_id_int)
                        account_manager.delete_account(account_id=account_id_int)
                    except SQLError as e:
                        print(f'Wystąpił błąd: {e}')
                        continue
                    except InvalidData as e:
                        print(f'Wystąpił błąd: {e}')
                        continue
                    break


            case 'E':
                try:
                    account_manager.show_account('')
                except SQLError as e:
                    print(f'\nWystąpił błąd: {e}')
                while True:
                    try:
                        account_id = input('Podaj ID konta, które chcesz edytować lub porzuć edycję [Q]: ')
                        if account_id.upper() == 'Q':
                            return None
                        account_id = validation.check_value(account_id, int, 'Numer konta powinien być liczbą.')
                    except InvalidData as e:
                        print(f'\nWystąpił błąd: {e}')
                        continue
                    try:
                        account_manager.check_record_existence(account_id=account_id)
                    except SQLError as e:
                        print(f'\nWystąpił błąd: {e}')
                        continue
                    break

                print('\nMożliwe do zmiany parametry konta:\n')
                print('1 - numer konta\n'
                      '2 - nazwa konta\n'
                      '3 - stan konta\n'
                      '4 - waluta\n'
                      'Q - porzuć edycję\n')

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
                            new_value = new_value.upper()
                            try:
                                validation.check_currency(new_value, 'Podano nieprawidłową walutę.')
                            except InvalidData as e:
                                print(f'Wystąpił błąd: {e}')
                                continue
                            break
                    break
                try:
                    account_manager.edit_account(account_id, parameter_to_change, new_value, param_to_change_from_user)
                except SQLError as e:
                    print(f'\nWystąpił błąd: {e}')
                print('\nZmiana została wykonana.')
            case 'P':
                while True:
                    account_id = input(
                        'Podaj numer id konta, którego szczegóły chcesz wyświetlić lub wciśnij enter, żeby zobaczyć wszystkie konta.')
                    if account_id:
                        try:
                            account_id = validation.check_value(account_id, int, 'ID powinno być liczbą.')
                        except InvalidData as e:
                            print(f'Wystąpił błąd: {e}')
                            continue
                    break
                try:
                    account_manager.show_account(account_id)
                except SQLError as e:
                    print(f'\nWystąpił błąd: {e}')
