from django import forms
from django.forms.models import inlineformset_factory
from .models import Transaction, SubTransaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['account', 'date', 'transaction_direction', 'description']

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
