from abc import ABC, abstractmethod


class MenuItem(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def get_submenu_items(self) -> list:
        pass


class UsersHandling(MenuItem):
    def __init__(self):
        super().__init__()
        self._name = 'Zarządzanie kontem użytkownika'
        self._letter = 'U'
        self._submenu_name = 'Menu obsługi użytkownika'

    @property
    def name(self):
        return self._name

    @property
    def letter(self):
        return self._letter

    @property
    def submenu_name(self):
        return self._submenu_name

    def get_submenu_items(self) -> dict[str:str]:
        return {'A': 'Add user', 'D': 'Delete user'}


class AccountHandling(MenuItem):
    def __init__(self):
        super().__init__()
        self._name = 'Zarządzanie kontem bankowym'
        self._letter = 'A'
        self._submenu_name = 'Menu obsługi konta bankowego'

    @property
    def name(self):
        return self._name

    @property
    def letter(self):
        return self._letter

    @property
    def submenu_name(self):
        return self._submenu_name

    def get_submenu_items(self) -> dict[str:str]:
        return {'A': 'Add account', 'D': 'Delete account'}
