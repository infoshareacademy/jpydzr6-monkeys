from abc import ABC, abstractmethod


class MenuItem(ABC):

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def letter(self):
        pass

    @property
    @abstractmethod
    def submenu_name(self):
        pass

    @abstractmethod
    def get_submenu_items(self) -> list:
        pass

    @abstractmethod
    def do_action(self, choice):
        pass


class UsersHandling(MenuItem):

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
