from dis import show_code

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
            raise WrongUserInput from None


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
            except WrongUserInput:
                print('\nNieprawidłowy wybór.\n')
                continue


if __name__ == '__main__':
    main()

# Notatki z chata
# # Sample list of instances from different classes
# instances = [instance1, instance2, instance3]  # Replace with your actual instances
#
# # Find the first instance with attribute 'U' using a generator expression
# selected_instance = next((instance for instance in instances if hasattr(instance, 'U')), None)
#
# # Output the result
# if selected_instance:
#     print("An instance with attribute 'U' was found:", selected_instance)
# else:
#     print("No instance with attribute 'U' found.")
