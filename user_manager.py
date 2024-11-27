"""
moduł zawierający klasę UserManager, która zarządza użytkownikami w bazie danych
'task: https://jira.is-academy.pl/browse/JPYDZR6MON-7'

"""


from peewee import *
from datetime import datetime
from hashlib import sha256
from typing import Optional, List, Tuple
from messages import *
import re
    

# Inicjalizacja bazy danych
db = SqliteDatabase('budget.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    DoesNotExist = None
    username = CharField(max_length=55, unique=True)
    password = CharField()
    email = CharField(unique=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'users'

class UserManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Haszuje hasło używając SHA-256."""
        return sha256(password.encode()).hexdigest()

    def setup_database(self):
        """Tworzy tabelę users jeśli nie istnieje."""
        db.connect()
        db.create_tables([User], safe=True)
        db.close()

    def add_user(self, username: str, password: str, email: str) -> bool:
        """
        Dodaje nowego użytkownika do bazy danych.
        Zwraca True jeśli się udało, False jeśli wystąpił błąd.
        """
        try:
            User.create(
                username=username,
                password=self.hash_password(password),
                email=email
            )
            return True
        except IntegrityError:
            print("Błąd: Użytkownik lub email już istnieje!")
            return False
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            return False

    def delete_user(self, user_id: int) -> bool:
        """
        Usuwa użytkownika o podanym ID.
        Zwraca True jeśli się udało, False jeśli wystąpił błąd.
        """
        try:
            query = User.delete().where(User.id == user_id)
            deleted_rows = query.execute()
            if deleted_rows > 0:
                return True
            print("Nie znaleziono użytkownika o podanym ID.")
            return False
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            return False

    def edit_user(self, user_id: int, email: Optional[str] = None, 
                  password: Optional[str] = None) -> bool:
        """
        Edytuje dane użytkownika.
        Zwraca True jeśli się udało, False jeśli wystąpił błąd.
        """
        try:
            user = User.get_by_id(user_id)
            if email:
                user.email = email
            if password:
                user.password = self.hash_password(password)
            user.save()
            return True
        except User.DoesNotExist:
            print("Nie znaleziono użytkownika o podanym ID.")
            return False
        except IntegrityError:
            print("Błąd: Email już istnieje!")
            return False
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            return False

    def login(self, username: str, password: str) -> Optional[User]:
        """
        Logowanie użytkownika.
        Zwraca obiekt User jeśli dane są poprawne, None w przeciwnym razie.
        """
        try:
            user = User.get(User.username == username)
            if user.password == self.hash_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None

    def show_users(self) -> List[tuple[int, str, str, datetime]]:
        """
        Zwraca listę wszystkich użytkowników.
        """
        users = []
        for user in User.select():
            users.append((user.id, user.username, user.email, user.created_at))
        return users

    @staticmethod
    def get_password_requirements() -> str:
        return PASSWORD_REQUIREMENTS

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        if len(password) < 8:
            return False, PASSWORD_TOO_SHORT
        
        if not any(c.isupper() for c in password):
            return False, PASSWORD_NO_UPPERCASE
            
        if not any(c.islower() for c in password):
            return False, PASSWORD_NO_LOWERCASE
            
        if not any(c.isdigit() for c in password):
            return False, PASSWORD_NO_DIGIT
            
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, PASSWORD_NO_SPECIAL
            
        return True, PASSWORD_OK

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Walidacja emaila używając regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, "Email jest poprawny"
        return False, "Nieprawidłowy format emaila"