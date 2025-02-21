from django import forms
from .models import MoneyAccount


class MoneyAccountForm(forms.ModelForm):
    balance = forms.FloatField(label='Saldo')
    class Meta:
        model = MoneyAccount
        fields = ['name', 'balance', 'type', 'currency_code', 'description']
        labels = {
            'name': 'Nazwa',
            'type': 'Typ',
            'currency_code': 'Kod waluty',
            'description': 'Opis',
        }

    description = forms.CharField(widget=forms.Textarea, required=False)
