from django import forms
from .models import MoneyAccount


class MoneyAccountForm(forms.ModelForm):
    class Meta:
        model = MoneyAccount
        fields = ['name', 'balance', 'type', 'currency_code', 'description']

    description = forms.CharField(widget=forms.Textarea, required=False)
