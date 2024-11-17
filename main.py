from menu import MenuItem

class WrongUserInput(Exception):
    pass


class Menu:
    def __init__(self):
        self._options: list[MenuItem] = [cls() for cls in MenuItem.__subclasses__()]
        self._options_dict: dict[str, MenuItem] = {cls.letter: cls for cls in self._options}

    @property
    def options(self):
        return self._options

    @property
    def options_dict(self):
        return self._options_dict

    def show_menu(self) -> None:
        print('Menu główne')
        for option in self.options:
            print(f'{option.letter} - {option.name}')
        print('Q - Wyjście z programu')

    def choose_menu_option(self, choice: str) -> MenuItem:
        try:
            chosen_menu_option = self._options_dict[choice]
        except KeyError:
            raise WrongUserInput('Wybór jest nieprawidłowy.') from None
        return chosen_menu_option

    @staticmethod
    def show_submenu(chosen_menu_option: MenuItem) -> None:
        submenu_items = chosen_menu_option.get_submenu_items()
        print(f'\n{chosen_menu_option.submenu_name}')
        for letter, name in (submenu_items.items()):
            print(f'{letter} - {name}')
        print('Q - Cofnij się do menu głównego')

    @staticmethod
    def validate_submenu_choice(submenu_choice: str, chosen_menu_option: MenuItem) -> None:
        try:
            chosen_menu_option.get_submenu_items()[submenu_choice]
        except KeyError:
            raise WrongUserInput('Wybór jest nieprawidłowy.') from None

    @staticmethod
    def do_chosen_action(submenu_choice: str, chosen_menu_option: MenuItem) -> None:
        chosen_menu_option.do_action(submenu_choice)


def main():
    action = Menu()
    print('\nWitaj w programie do budżetowania.\n')
    while True:
        action.show_menu()
        menu_choice = input('\nWybierz co chcesz zrobić: \n').upper()
        if menu_choice == 'Q':
            print('\nDo zobaczenia!')
            break
        try:
            chosen_menu_option = action.choose_menu_option(choice=menu_choice)
        except WrongUserInput as ex:
            print(f'\nWystąpił błąd: {ex}\n')
            continue
        while True:
            action.show_submenu(chosen_menu_option=chosen_menu_option)
            submenu_choice = input('\nWybierz co chcesz zrobić: \n').upper()
            if submenu_choice == 'Q':
                break
            try:
                action.validate_submenu_choice(submenu_choice=submenu_choice, chosen_menu_option=chosen_menu_option)
            except WrongUserInput as ex:
                print(f'\nWystąpił błąd: {ex}\n')
                continue
            action.do_chosen_action(submenu_choice=submenu_choice, chosen_menu_option=chosen_menu_option)
            continue

        continue


if __name__ == '__main__':
    main()
