from abc import ABC, abstractmethod


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
    def get_submenu_items(self) -> dict[str:str]: # przygotowuje słownik opcji dostępnych z submenu
        pass                                      # w formacie {'litera': 'nazwa opcji widziana w menu'}

    @abstractmethod
    def do_action(self, choice): # miejsce wywoływana konkretnych metod dostępnych z submenu
        pass


class UsersHandling(MenuItem):
    '''Przykładowa klasa dziedzicząca po MenuItem'''

    @property
    def name(self):
        return 'Zarządzanie kontem użytkownika'

    @property
    def letter(self):
        return 'U'

    @property
    def submenu_name(self):
        return 'Menu obsługi użytkownika'

    def get_submenu_items(self) -> dict[str:str]:
        return {'D': 'Dodaj użytkownika', 'U': 'Usuń użytkownika'}

    def do_action(self, choice):
        pass


class AccountHandling(MenuItem):
    '''Przykładowa klasa dziedzicząca po MenuItem'''

    @property
    def name(self):
        return 'Zarządzanie kontem bankowym'

    @property
    def letter(self):
        return 'A'

    @property
    def submenu_name(self):
        return 'Menu obsługi konta bankowego'

    def get_submenu_items(self) -> dict[str:str]:
        return {'D': 'Dodaj konto', 'U': 'Usuń konto'}

    def do_action(self, choice):
        pass
