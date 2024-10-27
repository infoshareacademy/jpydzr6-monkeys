from enum import Enum

class Actions(Enum):
    U = 'Zarządzanie użytkownikiem'
    K = 'Zarządzanie kontami bankowymi'
    T = 'Zarządzanie transakcjami'
    Z = 'Zarządzanie zadłużeniem'
    R = 'Wyświetl raport'
    Q = 'Wyjście z programu'


def choose_action():
    while True:
        print('Wybierz akcję do wykonania: \n')
        for action in Actions:
            print(f'{action.value} - {action.name}')
        choice = input().upper()

        try:
            action = Actions[choice]
        except KeyError:
            print('Podano nieprawidłową wartość.\n')
            continue

        print(action)
        return action


def main():
    print('Witaj w programie do budżetowania.\n')
    choose_action()

if __name__ == '__main__':
    main()
    