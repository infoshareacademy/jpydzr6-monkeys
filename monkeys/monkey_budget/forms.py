from django import forms
from .models import MoneyAccount
from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from .money import Monetary, CurrencyHelper
from .models import Transaction, SubTransaction
from decimal import Decimal


class MoneyAccountForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': '5', 'maxlength': 512}),
        required=False,
    )
    balance = forms.DecimalField(label='Saldo', decimal_places=2)

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
        label='Total amount',
        required=False,
        widget=forms.TextInput(
            attrs={'readonly': 'readonly', 'disabled': 'disabled', 'style': 'border: none; background: transparent;'}))
    balance_after_transaction_display = forms.CharField(
        label='Balance after transaction',
        required=False,
        widget=forms.TextInput(
            attrs={'readonly': 'readonly', 'disabled': 'disabled', 'style': 'border: none; background: transparent;'}))

    class Meta:
        model = Transaction
        fields = ['account', 'date', 'transaction_direction', 'description', 'total_display']
        widgets = {
            'description': forms.Textarea,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['total_display'].initial = Monetary(self.instance.total, self.instance.currency)
            self.fields['balance_after_transaction_display'].initial = Monetary(
                self.instance.balance_after_transaction,
                self.instance.currency)
        else:
            self.fields['total_display'].widget = forms.HiddenInput()
            self.fields['balance_after_transaction_display'].widget = forms.HiddenInput()


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
            'description': forms.Textarea,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = self.instance
        if instance.pk:
            currency = instance.main_transaction.currency
            currency_exponent = currency.get('exponent')

            self.fields['amount'] = forms.DecimalField(
                label='Amount',
                max_digits=19,
                decimal_places=currency_exponent,
                required=True,
                widget=DecimalWithDynamicPlacesWidget(decimal_places=currency_exponent)
            )
            self.fields['amount'].initial = Decimal(instance.amount / 10 ** currency_exponent)

    def clean(self):
        cleaned_data = super().clean()
        subtransaction = self.instance

        if self.instance.pk and self.cleaned_data.get('DELETE', False):
            transaction = subtransaction.main_transaction
            if transaction.subtransactions.count() == 1:
                raise forms.ValidationError('The transaction must consist of at least one subtransaction')

        return cleaned_data

    def clean_amount(self):
        if self.instance.pk:
            decimal_value = self.cleaned_data.get('amount')
            currency = self.instance.main_transaction.currency
            try:
                amount = float(decimal_value)
                amount = Monetary.major_to_minor_unit(amount, currency)
            except ValueError:
                raise forms.ValidationError("Amount must be a valid number.")

            return amount
        else:
            return self.cleaned_data.get('amount')


class SubTransactionBaseInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if self.total_form_count() == len(self.deleted_forms):
            raise forms.ValidationError('The subtransaction must consist of at least one subtransaction')


SubTransactionFormSet = inlineformset_factory(Transaction, SubTransaction, form=SubTransactionForm,
                                              formset=SubTransactionBaseInlineFormSet, min_num=1,
                                              can_delete=True)