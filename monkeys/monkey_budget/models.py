import decimal
from decimal import Decimal
from django.core.validators import ValidationError, MinValueValidator
from django.db import models, transaction
from django.db.models import Sum
from django.contrib.auth.models import User
import django.utils.timezone
from .money import Monetary, CurrencyHelper, Currency
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from .validator import validate_file_size

class UserProfile(models.Model):
    """
    Extended profile model for storing user avatars and additional information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


# Signal to automatically create a UserProfile when a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Check if the user has a profile first; if not, create one
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


class MoneyAccount(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    user_id = models.ForeignKey(User, related_name='money_accounts', on_delete=models.CASCADE, null=False)
    # krótka nazwa konta nadawana przez użytkownika np. 'Oszczędnościowe mbank'
    name = models.CharField(max_length=100)
    balance = models.BigIntegerField()
    #  typy przechowywania pieniędzy do wybrania przez użytkownika
    types = [('BA', 'konto bankowe'), ('CA', 'gotówka'), ('CO', 'bony'), ('AN', 'inne')]
    # typ konta do wybrania spośród podanych kategorii
    type = models.CharField(choices=types, max_length=50, default='konto bankowe')
    # ISO4217 np. PLN, USD
    currency_code = models.CharField(choices=CurrencyHelper.get_currencies_set(), max_length=3, default='PLN')
    # dłuższy opis konta dodawany przez użytkownika
    description = models.TextField(max_length=512)
    possibly_negative = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name}: {self.balance_formatted}'

    @property
    def currency(self) -> Currency:
        return CurrencyHelper.get_currency_by_its_code(self.currency_code)

    @property
    def balance_formatted(self) -> Monetary:
        return Monetary(self.balance, self.currency)

    def get_type_display_name(self):
        return dict(self.types).get(self.type, self.type)

    def validate_new_balance(self, new_balance: int) -> None | bool:
        if not self.possibly_negative and new_balance < 0:
            exceeding = Monetary(abs(new_balance), self.currency)
            raise ValidationError(f"Wybrane konto nie może posiadać ujemnego salda. "
                                  f"Transakcja przekracza saldo konta o {exceeding}.")
        return True


    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'Money Account'


class MainCategory(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    user_id = models.ForeignKey(User, related_name='main_categories', on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100)
    category_types = [
        ('INC', 'Przychód'),
        ('EXP', 'Wydatek'),
    ]
    category_type = models.CharField(choices=category_types, max_length=3)
    description = models.TextField(max_length=512, blank=True)

    def __str__(self):
        return f'{self.name} ({self.get_category_type_display()})'

    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'Main Category'
        verbose_name_plural = 'Main Categories'


class SubCategory(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    parent_category = models.ForeignKey(MainCategory, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=512, blank=True)

    def __str__(self):
        return f'{self.parent_category.name} - {self.name}'

    class Meta:
        app_label = 'monkey_budget'
        verbose_name = 'Sub Category'
        verbose_name_plural = 'Sub Categories'


class Transaction(models.Model):
    # TODO: Jeżeli konto miałoby zostać kiedyś usunięte to w przypadku, gdy posiada transakcje, być może powinno one
    #  zostać zarchiwizowane (dla raportów, w zależności jak będa one generowane lub dla zachowania faktur/paragonów
    #  związanych z gwarancją)
    account = models.ForeignKey(MoneyAccount, on_delete=models.deletion.CASCADE, related_name='transaction')
    date = models.DateTimeField(default=django.utils.timezone.now)
    total = models.BigIntegerField(
        validators=[MinValueValidator(
            limit_value=0,
            message='Transaction total value must be nonnegative')],
        default=0,
        editable=False)
    transaction_directions = [('IN', 'income'), ('OUT', 'outcome')]
    transaction_direction = models.CharField(choices=transaction_directions, max_length=3, default='OUT')
    balance_after_transaction = models.BigIntegerField(editable=False, default=0)
    description = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = 'monkey_budget'

    def __str__(self):
        money = Monetary(int(self.total), self.currency)
        return f"{self.transaction_direction} transaction of total {money}"

    @property
    def currency(self):
        return self.account.currency

    @property
    def total_formatted(self) -> Monetary:
        return Monetary(self.total, self.currency)

    @property
    def balance_after_transaction_formatted(self) -> Monetary:
        return Monetary(self.balance_after_transaction, self.currency)

    @staticmethod
    def calculate_new_account_balance(new_transaction_account, new_transaction, subtransactions) -> int:
        actual_account_balance = new_transaction_account.balance
        actual_transaction_total = new_transaction.total
        new_trasnaction_total = sum(subtransaction['amount'] for subtransaction in subtransactions)

        if new_transaction.transaction_direction == 'IN':
            previous_account_balance = actual_account_balance - actual_transaction_total
            new_balance_after_transaction = previous_account_balance + new_trasnaction_total
        else:
            previous_account_balance = actual_account_balance + actual_transaction_total
            new_balance_after_transaction = previous_account_balance - new_trasnaction_total
        return new_balance_after_transaction

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.pk:
                # Zapisz transakcję, aby dostać primary key
                # Nie liczymy sumy subtransakcji, bo one nie dostały jeszcze przypisanego klucza głównej transakcji
                super().save(*args, **kwargs)
            else:
                # Główna transakcja już jest zapisana w bazie, więc subtransakcję znają jej primary key.
                # Oblicz sumę subtransackji. Zwracane jest 0, jeśli nie ma subtransakcji, ale to jest tylko dla admina.W formularzu użytkownika zawsze musi byc jedna subtransakcja
                # Zaaktualizuj główną transakcję
                previous_total = self.total
                self.total = self.subtransactions.aggregate(Sum('amount'))['amount__sum'] or 0
                if self.transaction_direction == 'IN':
                    self.account.balance -= previous_total
                    self.balance_after_transaction = self.account.balance + self.total
                else:
                    self.account.balance += previous_total
                    self.balance_after_transaction = self.account.balance - self.total
                self.account.balance = self.balance_after_transaction
                self.account.save()
                super().save(*args, **kwargs)


class SubTransaction(models.Model):
    main_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.deletion.CASCADE,
        related_name='subtransactions')
    amount = models.BigIntegerField(
        validators=[MinValueValidator(
            limit_value=0,
            message='Subtransaction amount value must be nonnegative')])
    description = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = 'monkey_budget'

    def __str__(self):
        money = Monetary(int(self.amount), self.currency)
        return f"Part of transaction ({money})"

    @property
    def currency(self):
        return self.main_transaction.currency

    @property
    def amount_formatted(self) -> Monetary:
        return Monetary(self.amount, self.currency)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.main_transaction.pk:
                # Zapisz główną transakcję, aby mieć jej primary key
                self.main_transaction.save()
            # Zapisz subtransakcje
            super().save(*args, **kwargs)
            # Zaaktualizuj główną transakcję
            self.main_transaction.save()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            main_transaction = self.main_transaction

            super().delete(*args, **kwargs)
            main_transaction.save()


class UserRegistrationData(models.Model):
    """
    Model to store additional user registration data
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registration_data')
    ip_address = models.GenericIPAddressField(
        verbose_name=_('IP Address'),
        null=True,
        blank=True,
        help_text=_('IP address from which the user registered')
    )
    registration_date = models.DateTimeField(
        verbose_name=_('Registration Date'),
        auto_now_add=True,
        help_text=_('Date and time when the user registered')
    )
    user_agent = models.TextField(
        verbose_name=_('User Agent'),
        blank=True,
        help_text=_('Browser and system information of the user')
    )

    class Meta:
        verbose_name = _('User Registration Data')
        verbose_name_plural = _('User Registration Data')

    def __str__(self):
        return f"Registration data for {self.user.username}"

class TransactionAttachment(models.Model):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='attachments/',
        validators=[
            FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png']),
            validate_file_size
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment: {self.file.name}"
