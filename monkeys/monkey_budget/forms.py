from django import forms
from django.forms import inlineformset_factory

from .models import Transaction, SubTransaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction # total / balance_after_transaction rozliczane automatycznie
        fields = [
            'account',
            'date',
            'transaction_direction',
            'description',
        ]

SubTransactionFormset = inlineformset_factory(
    parent_model=Transaction,
    model=SubTransaction,
    fields=['amount', 'description'],
    extra = 1,
    can_delete = False,
)
