from examples import MenuItem

class Menu:
    def __init__(self):
        self._options = [cls() for cls in MenuItem.__subclasses__()]

    def show_menu(self):
        for option in self._options:
            print(f'{option.letter} - {option.name}')


def main():
    action = Menu()
    print('\nWitaj w programie do budżetowania.\n')
    action.show_menu()
    choice = input('\nWybierz co chcesz zrobić: ').upper()


if __name__ == '__main__':
    main()
