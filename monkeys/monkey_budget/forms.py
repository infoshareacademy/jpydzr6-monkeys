from django import forms
from .models import MoneyAccount
from .money import CurrencyHelper


class MoneyAccountForm(forms.ModelForm):
    class Meta:
        model = MoneyAccount
        fields = ['name', 'balance', 'type', 'currency_code', 'description']

    name = forms.CharField(
        max_length=100,
        label="Nazwa konta",
        widget=forms.TextInput(attrs={'placeholder': 'Podaj nazwę konta'})
    )
    balance = forms.IntegerField(
        label="Początkowy stan konta (liczba całkowita)",
        widget=forms.NumberInput()
    )
    type = forms.ChoiceField(
        choices=MoneyAccount.types,
        label="Typ konta",
        initial='BA'
    )
    currency_code = forms.ChoiceField(
        choices=CurrencyHelper.get_currencies_set(),
        label="Waluta",
        initial='PLN'
    )
    description = forms.CharField(
        max_length=512,
        label="Opis",
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Podaj krótki opis konta'})
    )
