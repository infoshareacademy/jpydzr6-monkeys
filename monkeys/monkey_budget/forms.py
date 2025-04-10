from .models import MoneyAccount
from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from .money import Monetary, Currency
from .models import Transaction, SubTransaction
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext as _


class MoneyAccountForm(forms.ModelForm):
    class Meta:
        model = MoneyAccount
        fields = ['name', 'balance', 'type', 'currency_code', 'description', 'possibly_negative']
        labels = {
            'name': 'Nazwa',
            'balance': 'Saldo',
            'type': 'Typ',
            'currency_code': 'Kod waluty',
            'description': 'Opis',
            'possibly_negative': 'Możliowść przyjęcia ujemnej wartości'
        }

    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': '5', 'maxlength': 512}),
        required=False,
    )

    balance = forms.DecimalField(label='Saldo', decimal_places=2)

    def __init__(self, *args, **kwargs):
        super(MoneyAccountForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['balance'].widget.attrs['readonly'] = True
            self.fields['balance'].widget.attrs['style'] = 'border: none;background: transparent;'

    def clean(self):
        cleaned_data = super().clean()
        balance = cleaned_data.get('balance')
        name = cleaned_data.get('name')
        all_accounts = MoneyAccount.objects.filter(user_id=2)
        allow_negative = cleaned_data.get('possibly_negative')

        if balance is not None and not allow_negative:
            if balance < 0:
                self.add_error(
                    'balance',
                    "Ujemna wartość nie jest dozwolona dla tego konta."
                )

        if not self.instance.pk:
            for account in all_accounts:
                if name == account.name:
                    self.add_error(
                        'name',
                        "Podana nazwa konta już istnieje."
                    )
        return cleaned_data


class MonetaryField(forms.DecimalField):
    def __init__(self, currency: Currency=None, *args, **kwargs):
        self.currency = currency
        super().__init__(*args, **kwargs)
        self.localize = True

    def prepare_value(self, value):
        if isinstance(value, Monetary):

            value = self.initial.amount_as_decimal
        return value

    def has_changed(self, initial, data):
        # Copied and adapted from original `has_changed()` method
        """Return True if data differs from initial."""
        # Always return False if the field is disabled since self.bound_data
        # always uses the initial value in this case.
        if self.disabled:
            return False
        try:
            data = self.to_python(data)
            if hasattr(self, "_coerce"):
                return self._coerce(data) != self._coerce(initial)
        except ValidationError:
            return True
        # For purposes of seeing whether something has changed, None is
        # the same as an empty string, if the data or initial value we get
        # is None, replace it with ''.
        initial_value = initial.amount_as_decimal if initial is not None else ""
        data_value = data if data is not None else ""
        return initial_value != data_value

    '''
    Poniższa walidacja jest propozycją, gdyby była wyamagana jakakolwiek po polsku. Póki co, nie udało mi się znaleźć
    szybkiego sposobu przetłumaczenia walidacji HTML5, która wyswietla się, gdy np. zostanie wpisana liczba zamiast liczby 
    '''
    # def validate(self, value):
    #     super().validate(value)
    #     if self.currency is not None:
    #         decimal_places = abs(value.as_tuple().exponent)
    #         if decimal_places > self.currency.get('exponent'):
    #             proposed_value = Monetary.major_to_minor_unit(value, self.currency)
    #             proposed_value = Monetary(proposed_value, self.currency).amount_as_decimal
    #             raise forms.ValidationError(
    #                 """
    #                 Wartość %(value)s przekracza ilość miejsc po przecinku dla wybranej waluty.
    #                 Czy chciałes wpisać %(proposed_value)s?
    #                 """,
    #                 code="invalid",
    #                 params={
    #                     "value": value,
    #                     "proposed_value": proposed_value
    #                 },
    #             )
    #     else:
    #         raise forms.ValidationError(
    #             "Brak przypisanej waluty subtransakcji!",
    #             code="invalid"
    #         )

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        if self.currency is not None:
            try:
                amount = Monetary.major_to_minor_unit(
                    value, self.currency)
                value = amount
            except ValueError:
                raise forms.ValidationError("Kwota musi być poprawną liczbą.")
        else:
            raise forms.ValidationError(
                "Brak przypisanej waluty subtransakcji!",
                code="invalid"
            )
        return value


class TransactionForm(forms.ModelForm):
    total_display = forms.CharField(
        label='Kwota łączna',
        required=False,
        widget=forms.TextInput(
            attrs={'readonly': 'readonly',
                   'disabled': 'disabled',
                   'style': 'border: none;background: transparent;'}))
    balance_after_transaction_display = forms.CharField(
        label='Saldo po transakcji',
        required=False,
        widget=forms.TextInput(
            attrs={'readonly': 'readonly',
                   'disabled': 'disabled',
                   'style': 'border: none; background: transparent;'}))

    class Meta:
        model = Transaction
        fields = ['account', 'date', 'transaction_direction', 'description', 'total_display']
        labels = {
            'account': 'Konto',
            'date': 'Data',
            'transaction_direction': 'Kierunek transakcji',
            'description': 'Opis',
        }
        widgets = {
            'description': forms.Textarea(
                attrs={'rows': '2'}
            )
        }
        Transaction._meta.get_field('transaction_direction').choices = [('IN', 'przychód'), ('OUT', 'wydatek')]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter accounts by user if provided
        if user:
            self.fields['account'].queryset = MoneyAccount.objects.filter(user_id=user)
        else:
            self.fields['account'].queryset = MoneyAccount.objects.none()

        if self.instance.pk:
            self.fields['total_display'].initial = Monetary(self.instance.total, self.instance.currency)
            self.fields['balance_after_transaction_display'].initial = Monetary(
                self.instance.balance_after_transaction,
                self.instance.currency)


class SubTransactionForm(forms.ModelForm):
    amount_decimal = MonetaryField(
        required=True,
        label='Kwota',
    )

    class Meta:
        model = SubTransaction
        fields = ['amount_decimal', 'description']
        widgets = {
            'description': forms.Textarea(
                attrs={'rows': '2'}
            )
        }
        labels = {
            'amount': 'Kwota',
            'description': 'Opis',
        }

    def __init__(self, main_transaction_account=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if instance and instance.pk:
            self.currency = instance.currency
            self.fields['amount_decimal'] = MonetaryField(
                required=True,
                label='Kwota',
                currency=self.currency,
                decimal_places=self.currency.get('exponent')
            )
            self.fields['amount_decimal'].initial = Monetary(instance.amount, self.currency)
        elif main_transaction_account:
            self.currency = main_transaction_account.currency
            self.fields['amount_decimal'] = MonetaryField(
                required=True,
                label='Kwota',
                currency=self.currency,
                decimal_places=self.currency.get('exponent'),
            )

    def clean(self):
        cleaned_data = super().clean()
        subtransaction = self.instance

        if self.instance.pk and self.cleaned_data.get('DELETE', False):
            transaction = subtransaction.main_transaction
            if transaction.subtransactions.count() == 1:
                raise forms.ValidationError('Transakcja musi posiadać przynajmniej jedną subtransakcję')

        cleaned_data['amount'] = self.cleaned_data.get('amount_decimal')
        return cleaned_data

    def save(self, commit=True):
        # Ta metoda save służy do przepisania skonwertowanej wartości z decimal na int.
        # Nie wchodzi w zakres zadań metody save() w modelu
        # ni robimy też tego w widoku, ponieważ wtedy nie dałoby rady zapisywać w django admin
        instance = super().save(commit=False)
        instance.amount = self.cleaned_data.get('amount_decimal')

        if commit:
            instance.save()
        return instance


class SubTransactionBaseInlineFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if 'DELETE' in form.fields:
            form.fields['DELETE'].label = "Usuń"

    def clean(self):
        super().clean()

        if self.total_form_count() == len(self.deleted_forms):
            raise forms.ValidationError('Transakcja musi posiadać przynajmniej jedną subtransakcję')

        if self.is_valid():
            if self.instance.pk:
                main_transaction_account = self.instance.account
            else:
                main_transaction_account = self.form_kwargs.get('main_transaction_account')
            main_transaction = self.instance
            subtransactions = [subtransaction for subtransaction in self.cleaned_data  if subtransaction]
            requested_account_balance_after_transaction = Transaction.calculate_new_account_balance(main_transaction_account, main_transaction, subtransactions)
            main_transaction_account.validate_new_balance(requested_account_balance_after_transaction)


SubTransactionFormSet = inlineformset_factory(
    Transaction,
    SubTransaction,
    form=SubTransactionForm,
    formset=SubTransactionBaseInlineFormSet,
    min_num=1,
    can_delete=True,
)        




class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    privacy_policy = forms.BooleanField(
        required=True,
        label=_("Zgadzam się na politykę prywatności"),
        help_text=_("Musisz zgodzić się na politykę prywatności")
    )
    terms = forms.BooleanField(
        required=True,
        label=_("Zgadzam się na warunki użytkowania"),
        help_text=_("Musisz zgodzić się na warunki użytkowania")
    )
    rodo = forms.BooleanField(
        required=True,
        label=_("Zgadzam się na przetwarzanie danych osobowych (GDPR/RODO)"),
        help_text=_("Musisz zgodzić się na przetwarzanie danych osobowych")
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'privacy_policy', 'terms', 'rodo']

    def clean(self):
        cleaned_data = super().clean()
        privacy_policy = cleaned_data.get('privacy_policy')
        terms = cleaned_data.get('terms')
        rodo = cleaned_data.get('rodo')

        if not privacy_policy:
            self.add_error('privacy_policy', _("Musisz zgodzić się na politykę prywatności"))
        if not terms:
            self.add_error('terms', _("Musisz zgodzić się na warunki użytkowania"))
        if not rodo:
            self.add_error('rodo', _("Musisz zgodzić się na przetwarzanie danych osobowych"))

        return cleaned_data

    def save(self, commit=True):   
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = False  # User will be inactive until email is verified
        if commit:
            user.save()
        return user
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("Ten adres email jest już w użyciu."))
        return email



class UserUpdateForm(forms.ModelForm):
    """Form for updating user data in the profile"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        
    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        # Add the 'form-control' class to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # If the user has a profile with an avatar, get it
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['avatar'].initial = self.instance.profile.avatar


class PasswordResetRequestForm(forms.Form):
    """
    Form for requesting password reset via email
    """
    email = forms.EmailField(
        label="Email",
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Podaj adres email',
                'autocomplete': 'email'
            }
        )
    )


class SetPasswordForm(forms.Form):
    """
    Form for setting a new password
    """
    new_password1 = forms.CharField(
        label="Nowe hasło",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Wprowadź nowe hasło'),
                'autocomplete': 'new-password'
            }
        ),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Powtórz nowe hasło",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Powtórz nowe hasło'),
                'autocomplete': 'new-password'
            }
        ),
        strip=False,
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Hasła nie pasują do siebie"))
        return password2


class MagicLinkLoginForm(forms.Form):
    """
    Form for requesting magic link login via email
    """
    email = forms.EmailField(
        label="Email",
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Podaj adres email'),
                'autocomplete': 'email'
            }
        )
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("Nie znaleziono użytkownika z tym adresem email"))
        return email


class ResendActivationForm(forms.Form):
    """Form for resending account activation email"""
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Podaj adres email')
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email, is_active=False)
        except User.DoesNotExist:
            raise forms.ValidationError(_('Nie znaleziono nieaktywnego konta z tym adresem email.'))
        return email
