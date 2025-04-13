## python manage.py generate_sample_data
## Username: test_user
## Password: testpass123
## mkdir -p monkeys/monkey_budget/management/commands
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from monkey_budget.models import MoneyAccount, MainCategory, SubCategory, Transaction, SubTransaction
from decimal import Decimal
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Generuje przykładowe dane do testów'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generowanie przykładowych danych...')
        
        # Tworzenie użytkownika testowego
        test_user, created = User.objects.get_or_create(
            username='test_user',
            email='test@example.com'
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            self.stdout.write('Utworzono użytkownika testowego: test_user / testpass123')
        
        # Dane przykładowych kont
        accounts_data = [
            {
                'name': 'Santander',
                'balance': 500000,  # 5000 PLN
                'type': 'BA',
                'currency_code': 'PLN',
                'description': 'Konto w Santander Bank Polska',
                'possibly_negative': True
            },
            {
                'name': 'ING',
                'balance': 1000000,  # 10000 PLN
                'type': 'BA',
                'currency_code': 'PLN',
                'description': 'Konto w ING Bank Śląski',
                'possibly_negative': False
            },
            {
                'name': 'Alior',
                'balance': 300000,  # 3000 PLN
                'type': 'BA',
                'currency_code': 'PLN',
                'description': 'Konto w Alior Bank',
                'possibly_negative': True
            },
            {
                'name': 'Gotówka w domu',
                'balance': 10000,  # 100 PLN
                'type': 'CA',
                'currency_code': 'PLN',
                'description': 'Gotówka przechowywana w domu',
                'possibly_negative': False
            }
        ]
        
        # Tworzenie kont
        accounts = []
        for acc_data in accounts_data:
            account, created = MoneyAccount.objects.get_or_create(
                user_id=test_user,
                name=acc_data['name'],
                defaults={
                    'balance': acc_data['balance'],
                    'type': acc_data['type'],
                    'currency_code': acc_data['currency_code'],
                    'description': acc_data['description'],
                    'possibly_negative': acc_data['possibly_negative']
                }
            )
            accounts.append(account)
            if created:
                self.stdout.write(f'Utworzono konto: {account.name}')
        
        # Dane przykładowych kategorii
        categories_data = [
            {
                'name': 'Przychody',
                'category_type': 'INC',
                'description': 'Źródła regularnych przychodów',
                'subcategories': [
                    {'name': 'Wynagrodzenie', 'description': 'Miesięczna wypłata'},
                    {'name': 'Freelance', 'description': 'Dochody z pracy dodatkowej'},
                    {'name': 'Inwestycje', 'description': 'Zwroty z inwestycji'},
                    {'name': 'Premia', 'description': 'Premie i dodatki'},
                    {'name': '13. emerytura', 'description': 'Dodatkowa emerytura'},
                    {'name': '500+', 'description': 'Świadczenie rodzinne'},
                    {'name': 'Sprzedaż', 'description': 'Sprzedaż przedmiotów'},
                    {'name': 'Darowizna', 'description': 'Darowizny i prezenty pieniężne'}
                ]
            },
            {
                'name': 'Wydatki',
                'category_type': 'EXP',
                'description': 'Regularne wydatki',
                'subcategories': [
                    {'name': 'Żywność', 'description': 'Zakupy spożywcze i restauracje'},
                    {'name': 'Transport', 'description': 'Koszty transportu'},
                    {'name': 'Rachunki', 'description': 'Rachunki i opłaty'},
                    {'name': 'Rozrywka', 'description': 'Rozrywka i hobby'},
                    {'name': 'Zdrowie', 'description': 'Wydatki na zdrowie'},
                    {'name': 'Ubrania', 'description': 'Zakupy odzieżowe'},
                    {'name': 'Mieszkanie', 'description': 'Wydatki związane z mieszkaniem'},
                    {'name': 'Edukacja', 'description': 'Wydatki na edukację'},
                    {'name': 'Kredyty', 'description': 'Raty kredytów'},
                    {'name': 'Ubezpieczenia', 'description': 'Składki ubezpieczeniowe'},
                    {'name': 'Kościół', 'description': 'Ofiary kościelne'},
                    {'name': 'Prezenty', 'description': 'Prezenty dla bliskich'},
                    {'name': 'Wakacje', 'description': 'Wydatki na wakacje'},
                    {'name': 'Remont', 'description': 'Wydatki na remont'},
                    {'name': 'Zwierzęta', 'description': 'Wydatki na zwierzęta'}
                ]
            }
        ]
        
        # Tworzenie kategorii i podkategorii
        categories = []
        for cat_data in categories_data:
            category, created = MainCategory.objects.get_or_create(
                user_id=test_user,
                name=cat_data['name'],
                defaults={
                    'category_type': cat_data['category_type'],
                    'description': cat_data['description']
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Utworzono kategorię: {category.name}')
                
                # Tworzenie podkategorii
                for subcat_data in cat_data['subcategories']:
                    subcategory = SubCategory.objects.create(
                        parent_category=category,
                        name=subcat_data['name'],
                        description=subcat_data['description']
                    )
                    self.stdout.write(f'Utworzono podkategorię: {subcategory.name}')
        
        # Generowanie przykładowych transakcji z ostatnich 30 dni
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Przykładowe opisy transakcji
        income_descriptions = [
            'Wypłata',
            'Projekt IT',
            'Dywidenda',
            'Premia kwartalna',
            'Nadgodziny',
            'Zwrot podatku',
            '13. emerytura',
            'Świadczenie 500+',
            'Sprzedaż na Allegro',
            'Darowizna rodzinna',
            'Freelance - projekt',
            'Korepetycje',
            'Wynajem mieszkania',
            'Odsetki z lokaty'
        ]
        
        expense_descriptions = [
            'Zakupy w Biedronce',
            'Obiad w restauracji',
            'Bilet miesięczny',
            'Rachunek za prąd',
            'Abonament internetowy',
            'Bilety do kina',
            'Karnet na siłownię',
            'Leki w aptece',
            'Czynsz',
            'Zakupy w Lidlu',
            'Zakupy w Kauflandzie',
            'Zakupy w Żabce',
            'Bilet PKP',
            'Bilet MPK',
            'Tankowanie paliwa',
            'Rachunek za gaz',
            'Rachunek za wodę',
            'Rachunek za telefon',
            'Netflix',
            'Spotify',
            'Wizyta u lekarza',
            'Wizyta u dentysty',
            'Zakupy w H&M',
            'Zakupy w Reserved',
            'Zakupy w CCC',
            'Rata kredytu hipotecznego',
            'Rata kredytu samochodowego',
            'Składka OC/AC',
            'Składka na życie',
            'Ofiara na tacę',
            'Prezent urodzinowy',
            'Prezent świąteczny',
            'Wakacje nad morzem',
            'Wakacje w górach',
            'Materiały budowlane',
            'Usługi remontowe',
            'Karma dla psa',
            'Weterynarz'
        ]
        
        # Generowanie transakcji
        for _ in range(50):  # Generowanie 50 losowych transakcji
            # Losowa data między start_date i end_date
            transaction_date = start_date + timedelta(
                seconds=random.randint(0, int((end_date - start_date).total_seconds()))
            )
            
            # Losowe konto
            account = random.choice(accounts)
            
            # Losowy typ kategorii (przychód lub wydatek)
            category_type = random.choice(['INC', 'EXP'])
            category = random.choice([c for c in categories if c.category_type == category_type])
            subcategory = random.choice(list(category.subcategories.all()))
            
            # Losowa kwota (między 1000 a 50000 - 10 PLN do 500 PLN)
            amount = random.randint(1000, 50000)
            
            # Tworzenie transakcji
            transaction = Transaction.objects.create(
                account=account,
                date=transaction_date,
                transaction_direction='IN' if category_type == 'INC' else 'OUT',
                description=random.choice(income_descriptions if category_type == 'INC' else expense_descriptions)
            )
            
            # Tworzenie podtransakcji
            SubTransaction.objects.create(
                main_transaction=transaction,
                amount=amount,
                description=f'{subcategory.name} - {transaction.description}'
            )
            
            self.stdout.write(f'Utworzono transakcję: {transaction.description} - {amount/100} PLN')
        
        self.stdout.write(self.style.SUCCESS('Pomyślnie wygenerowano przykładowe dane')) 
        