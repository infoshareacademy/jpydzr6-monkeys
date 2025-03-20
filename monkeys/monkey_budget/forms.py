from django import forms
from .models import MoneyAccount
from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from .money import Monetary, Currency
from .models import Transaction, SubTransaction
from decimal import Decimal


class MoneyAccountForm(forms.ModelForm):

    class Meta:
        model = MoneyAccount
        fields = ['name', 'balance', 'type', 'currency_code', 'description', 'possibly_negative']
        labels = {
            'name': 'Nazwa',
            'type': 'Typ',
            'currency_code': 'Kod waluty',
            'description': 'Opis',
            'possibly_negative': 'Możliowść przyjęcia ujemnej wartości'
        }

        balance = forms.DecimalField(label='Saldo', decimal_places=2)
        # description = forms.CharField(
        #     # widget=forms.Textarea,
        #     required=False,
        #     label='Opis',
        #     max_length=512)

        widgets = {
            'description': forms.Textarea(
                attrs={
                    'rows': '5',
                    # 'required': False,
                    # 'maxlength': 512,
                },


            )
        }



    def __init__(self, *args, **kwargs):
        super(MoneyAccountForm, self).__init__(*args, **kwargs)

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

        data = Decimal(data)
        data = Monetary.major_to_minor_unit(data, self.currency)
        # For purposes of seeing whether something has changed, None is
        # the same as an empty string, if the data or initial value we get
        # is None, replace it with ''.
        initial_value = initial if initial is not None else ""
        data_value = data if data is not None else ""
        return initial_value != data_value


class MonetaryWidget(forms.NumberInput):
    def __init__(self, currency:Currency, *args, **kwargs):
        self.currency = currency
        super().__init__(*args, **kwargs)

    def format_value(self, value):
        if value is None:
            return ''
        elif isinstance(value, int):
            return f"{Monetary(value, self.currency).amount_as_decimal}"
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

    def __init__(self, main_transaction_form_cleaned_data=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_transaction_form_cleaned_data = main_transaction_form_cleaned_data

        self.fields['amount'] = forms.DecimalField(
            label='Kwota',
            max_digits=19,
            required=True,
            widget=forms.NumberInput(attrs={'step': 'any'})
        )

        instance = self.instance
        if instance.pk:
            currency = instance.main_transaction.currency
            currency_exponent = currency.get('exponent')

            self.fields['amount'] = MonetaryField(
                label='Kwota',
                max_digits=19,
                decimal_places=currency_exponent,
                required=True,
                widget=MonetaryWidget(currency),
                currency=currency
            )
            self.fields['amount'].initial = Monetary(instance.amount, currency) #Decimal(instance.amount) / Decimal(10 ** currency_exponent)

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
            currency = self.instance.main_transaction.currency
        else:
            currency = self.main_transaction_form_cleaned_data.get('account').currency
        try:
            amount = Monetary.major_to_minor_unit(
                self.cleaned_data.get('amount'),
                currency)
        except ValueError:
            raise forms.ValidationError("Kwota musi być poprawną liczbą.")
        return amount
        # else:
        #     return self.cleaned_data.get('amount')


class SubTransactionBaseInlineFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if 'DELETE' in form.fields:
            form.fields['DELETE'].label = "Usuń"

    def clean(self):
        super().clean()
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
