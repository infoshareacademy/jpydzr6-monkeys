from datetime import date, timedelta
from .models import MoneyAccount
from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from .money import Monetary, Currency, CurrencyHelper
from .models import Transaction, SubTransaction
from decimal import Decimal


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

    def clean(self):
        cleaned_data = super().clean()
        balance = cleaned_data.get('balance')
        allow_negative = cleaned_data.get('possibly_negative')

        if balance is not None and not allow_negative:
            if balance < 0:
                self.add_error(
                    'balance',
                    "Ujemna wartość nie jest dozwolona dla tego konta."
                )
        return cleaned_data


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
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['total_display'].initial = Monetary(self.instance.total, self.instance.currency)
            self.fields['balance_after_transaction_display'].initial = Monetary(
                self.instance.balance_after_transaction,
                self.instance.currency)


class MonetaryField(forms.DecimalField):
    def __init__(self, currency: Currency, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.currency = currency

    def has_changed(self, initial, data):
        super().has_changed(initial, data)
        data = Monetary.major_to_minor_unit(data, self.currency)
        # For purposes of seeing whether something has changed, None is
        # the same as an empty string, if the data or initial value we get
        # is None, replace it with ''.
        initial_value = initial if initial is not None else ""
        data_value = data if data is not None else ""
        return initial_value != data_value


class DecimalWithDynamicPlacesWidget(forms.NumberInput):
    def __init__(self, decimal_places, *args, **kwargs):
        self.decimal_places = decimal_places
        super().__init__(*args, **kwargs)

    def format_value(self, value):
        if value is None:
            return ''
        elif isinstance(value, int):
            return f"{Decimal(value / 10 ** self.decimal_places):.{self.decimal_places}f}"
        else:
            return value


class SubTransactionForm(forms.ModelForm):
    class Meta:
        model = SubTransaction
        fields = ['amount', 'description']
        widgets = {
            'description': forms.Textarea(
                attrs={'rows': '2'}
            )
        }
        labels = {
            'amount': 'Kwota',
            'description': 'Opis',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = self.instance
        if instance.pk:
            currency = instance.main_transaction.currency
            currency_exponent = currency.get('exponent')

            self.fields['amount'] = MonetaryField(
                label='Kwota',
                max_digits=19,
                decimal_places=currency_exponent,
                required=True,
                widget=DecimalWithDynamicPlacesWidget(decimal_places=currency_exponent),
                currency=currency
            )
            self.fields['amount'].initial = Decimal(instance.amount) / Decimal(10 ** currency_exponent)

    def clean(self):
        cleaned_data = super().clean()
        subtransaction = self.instance

        if self.instance.pk and self.cleaned_data.get('DELETE', False):
            transaction = subtransaction.main_transaction
            if transaction.subtransactions.count() == 1:
                raise forms.ValidationError('Transakcja musi posiadać przynajmniej jedną subtransakcję')

        return cleaned_data

    def clean_amount(self):
        if self.instance.pk:
            try:
                amount = Monetary.major_to_minor_unit(
                    self.cleaned_data.get('amount'),
                    self.instance.main_transaction.currency)
            except ValueError:
                raise forms.ValidationError("Kwota musi być poprawną liczbą.")
            return amount
        else:
            return self.cleaned_data.get('amount')


class SubTransactionBaseInlineFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if 'DELETE' in form.fields:
            form.fields['DELETE'].label = "Usuń"

    def clean(self):
        super().clean()
        main_transaction = self.instance
        subtransactions = [subtransaction for subtransaction in self.cleaned_data  if subtransaction]
        requested_account_balance_after_transaction = Transaction.calculate_new_account_balance(main_transaction, subtransactions)
        main_transaction.account.validate_new_balance(requested_account_balance_after_transaction)

        if self.total_form_count() == len(self.deleted_forms):
            raise forms.ValidationError('Transakcja musi posiadać przynajmniej jedną subtransakcję')


SubTransactionFormSet = inlineformset_factory(
    Transaction,
    SubTransaction,
    form=SubTransactionForm,
    formset=SubTransactionBaseInlineFormSet,
    min_num=1,
    can_delete=True,
)

class FinancialReport(forms.Form):

    account_name = forms.ModelMultipleChoiceField(
        queryset=MoneyAccount.objects.all().filter(user_id=2).order_by('name'),
        label='Wybierz konto',
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    transactions_direction = forms.MultipleChoiceField(
        choices=[('IN', 'przychód'), ('OUT', 'wydatek')],
        label='Wybierz kierunek transakcji',
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    currency = forms.MultipleChoiceField(
        choices=CurrencyHelper.get_currencies_set(),
        label='Wybierz kod waluty',
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    start_date = forms.DateField(
        label='Data początkowa',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}), initial=(date.today() - timedelta(days=30))
    )
    end_date = forms.DateField(
        label='Data końcowa',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}), initial=date.today
    )

class MonthlyFinancialReport(forms.Form):
    MONTH_CHOICES = [
        (1, "Styczeń"), (2, "Luty"), (3, "Marzec"),
        (4, "Kwiecień"), (5, "Maj"), (6, "Czerwiec"),
        (7, "Lipiec"), (8, "Sierpień"), (9, "Wrzesień"),
        (10, "Październik"), (11, "Listopad"), (12, "Grudzień")
    ]
    month = forms.ChoiceField(choices=MONTH_CHOICES, label="Wybierz miesiąc")
    year = forms.IntegerField(label="Wybierz rok", min_value=1900, max_value=2100)
