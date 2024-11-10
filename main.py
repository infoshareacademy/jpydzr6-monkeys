from examples import MenuItem

class WrongUserInput(Exception):
    pass


class Menu:
    def __init__(self):
        self._options = [cls() for cls in MenuItem.__subclasses__()]
        self._options_dict = {cls.letter: cls.name for cls in self._options}

    @property
    def options(self):
        return self._options

    @property
    def options_dict(self):
        return self._options_dict

    def show_menu(self) -> None:
        for option in self.options:
            print(f'{option.letter} - {option.name}')
        print('Q - Wyjście z programu')

    def show_submenu(self, choice: str):
        try:
            return self._options_dict[choice]
        except KeyError:
            raise WrongUserInput('Wybór jest nieprawidłowy.') from None

def main():
    action = Menu()
    print('\nWitaj w programie do budżetowania.\n')
    while True:
        action.show_menu()
        choice = input('\nWybierz co chcesz zrobić: ').upper()
        if choice == 'Q':
            print('\nDo zobaczenia!')
            break
        else:
            try:
                action.show_submenu(choice=choice)
            except WrongUserInput as ex:
                print(f'\nWystąpił błąd: {ex}\n')
                continue


if __name__ == '__main__':
    main()
