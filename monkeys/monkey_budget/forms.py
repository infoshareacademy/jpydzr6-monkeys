from django import forms
from .models import MoneyAccount
from .money import CurrencyHelper


class AddMoneyAccountForm(forms.ModelForm):
    class Meta:
        model = MoneyAccount
        fields = ['name', 'balance', 'type', 'currency_code', 'description']

    description = forms.CharField(widget=forms.Textarea, required=False)


class EditMoneyAccountForm(forms.ModelForm):
    class Meta:
        model = MoneyAccount
        fields = ['name', 'balance', 'type', 'currency_code', 'description']

    description = forms.CharField(widget=forms.Textarea, required=False)
