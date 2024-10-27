from enum import Enum


class Actions(Enum):
    U = 'Zarządzanie użytkownikiem'
    K = 'Zarządzanie kontami bankowymi'
    T = 'Zarządzanie transakcjami'
    Z = 'Zarządzanie zadłużeniem'
    R = 'Wyświetl raport'
    Q = 'Wyjście z programu'


def choose_action() -> Actions:
    while True:
        print('Wybierz akcję do wykonania: \n')
        for action in Actions:
            print(f'{action.value} - {action.name}')
        choice = input().upper()

        try:
            action = Actions[choice]
        except KeyError:
            print('Niepoprawna komenda.\n')
            continue
        print(type(action))
        return action


def do_action(action: Actions) -> None:
    match action:
        case Actions.U:
            print('U')
        case Actions.K:
            print('K')
        case Actions.T:
            print('T')
        case Actions.Z:
            print('Z')
        case Actions.R:
            print('R')


def main() -> None:
    print('Witaj w programie do budżetowania.\n')
    while True:
        action = choose_action()
        if action == Actions.Q:
            print('Do zobaczenia!')
            break
        else:
            do_action(action=action)


if __name__ == '__main__':
    main()
    