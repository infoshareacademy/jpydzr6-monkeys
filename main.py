from examples import MenuItem

class WrongUserInput(Exception):
    pass


class Menu:
    def __init__(self):
        self._options = [cls() for cls in MenuItem.__subclasses__()]
        self._options_dict = {cls.letter: cls for cls in self._options}

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

    def show_submenu(self, choice: str):
        try:
            submenu_instance = self._options_dict[choice]
        except KeyError:
            raise WrongUserInput('Wybór jest nieprawidłowy.') from None
        else:
            submenu_items = submenu_instance.get_submenu_items()
            print(f'\n{submenu_instance.submenu_name}')
            for letter, name in submenu_items.items():
                print(f'{letter} - {name}')
            print('Q - Cofnij się do menu głównego')

def main():
    action = Menu()
    print('\nWitaj w programie do budżetowania.\n')
    while True:
        action.show_menu()
        menu_choice = input('\nWybierz co chcesz zrobić: \n').upper()
        if menu_choice == 'Q':
            print('\nDo zobaczenia!')
            break
        else:
            try:
                action.show_submenu(choice=menu_choice)
            except WrongUserInput as ex:
                print(f'\nWystąpił błąd: {ex}\n')
                continue
            else:
                submenu_choice = input('\nWybierz co chcesz zrobić: \n').upper()
                if submenu_choice == 'Q':
                    continue

        break # todo pamiętaj o usunięciu tego break

# todo trzeba jeszcze obsłużyć sytuację błędnego wyboru opcji z submenu

if __name__ == '__main__':
    main()
