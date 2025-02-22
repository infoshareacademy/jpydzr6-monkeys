from django import forms
from django.forms.models import inlineformset_factory
from .money import Monetary, CurrencyHelper
from .models import Transaction, SubTransaction


class TransactionForm(forms.ModelForm):
    total_display = forms.CharField(label='Total amount', required=False, widget=forms.TextInput(
        attrs={'readonly': 'readonly', 'disabled': 'disabled', 'style': 'border: none; background: transparent;'}))
    balance_after_transaction_display = forms.CharField(label='Balance after transaction', required=False,
                                                        widget=forms.TextInput(
                                                            attrs={'readonly': 'readonly', 'disabled': 'disabled',
                                                                   'style': 'border: none; background: transparent;'}))

    class Meta:
        model = Transaction
        fields = ['account', 'date', 'transaction_direction', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            currency = CurrencyHelper.get_currency_by_its_code(self.instance.account.currency_code)
            self.fields['total_display'].initial = Monetary(self.instance.total, currency)
            self.fields['balance_after_transaction_display'].initial = Monetary(self.instance.balance_after_transaction,
                                                                                currency)
        else:
            self.fields['total_display'].widget = forms.HiddenInput()
            self.fields['balance_after_transaction_display'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        main_transaction = self.instance

        # Parent musi mieć przynajmniej jedną subtransakcję
        if main_transaction.pk:
            if not main_transaction.subtransactions.exists():
                raise forms.ValidationError('The transaction must consist of at least one subtransaction')

        return cleaned_data


class SubTransactionForm(forms.ModelForm):
    class Meta:
        model = SubTransaction
        fields = ['amount', 'description']

    def clean(self):
        cleaned_data = super().clean()
        subtransaction = self.instance

        if self.instance.pl and self.cleaned_data.get('DELETE', False):
            transaction = subtransaction.main_transaction
            if transaction.subtransactions.count() == 1:
                raise forms.ValidationError('The transaction must consist of at least one subtransaction')

        return cleaned_data


SubtransactionFormSet = inlineformset_factory(Transaction, SubTransaction, form=SubTransactionForm, min_num=1,
                                              can_delete=True)
