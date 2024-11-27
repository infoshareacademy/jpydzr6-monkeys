"""
scrypt testowy umożliwiający testowanie user_manager.py

"""



from user_manager import UserManager
from messages import MAIN_MENU


def main():
    # Inicjalizacja managera użytkowników
    manager = UserManager()
    manager.setup_database()

    while True:
        print(MAIN_MENU)
        choice = input("Wybierz opcję: ")

        if choice == "1":
            username = input("Podaj nazwę użytkownika: ")
            print("Wymagania dotyczące hasła:")
            print(UserManager.get_password_requirements())
            
            while True:
                password = input("Podaj hasło: ")
                is_valid, message = UserManager.validate_password(password)
                print(message)
                if is_valid:
                    break
                print("\nSpróbuj ponownie.")
            
            while True:
                email = input("Podaj email: ")
                is_valid, message = UserManager.validate_email(email)
                print(message)
                if is_valid:
                    break
                print("\nPopraw email.")
            
            if manager.add_user(username, password, email):
                print("Użytkownik dodany pomyślnie!")

        elif choice == "2":
            user_id = int(input("Podaj ID użytkownika do usunięcia: "))
            if manager.delete_user(user_id):
                print("Użytkownik usunięty pomyślnie!")

        elif choice == "3":
            user_id = int(input("Podaj ID użytkownika do edycji: "))
            email = input("Podaj nowy email (Enter aby pominąć): ")
            password = input("Podaj nowe hasło (Enter aby pominąć): ")

            email = email if email else None
            password = password if password else None

            if manager.edit_user(user_id, email, password):
                print("Dane użytkownika zaktualizowane pomyślnie!")

        elif choice == "4":
            users = manager.show_users()
            print("\nLista użytkowników:")
            print("ID  |  Username  |  Email")
            print("-" * 40)
            for user_id, username, email, created_at in users:
                print(f"{user_id:3} | {username:10} | {email} | {created_at}")

        elif choice == "5":
            username = input("Podaj nazwę użytkownika: ")
            password = input("Podaj hasło: ")
            user = manager.login(username, password)
            if user:
                print(f"Zalogowano pomyślnie jako {user.username}!")
            else:
                print("Błędne dane logowania!")

        elif choice == "0":
            print("Do widzenia!")
            break

        else:
            print("Nieprawidłowa opcja!")


if __name__ == "__main__":
    main()