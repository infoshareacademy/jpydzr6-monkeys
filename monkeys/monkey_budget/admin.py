from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import MoneyAccount, Transaction, SubTransaction
from .forms import TransactionForm, SubTransactionFormSet, SubTransactionForm
from .money import Monetary, CurrencyHelper

admin.site.register(MoneyAccount)


class SubTransactionInline(admin.TabularInline):
    model = SubTransaction
    form = SubTransactionForm
    formset = SubTransactionFormSet
    min_num = 1
    extra = 0
    can_delete = True


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    form = TransactionForm
    list_display = ['total_display', 'transaction_direction', 'account']
    search_fields = ['account']
    list_filter = ['transaction_direction', 'date']
    inlines = [SubTransactionInline]

    def total_display(self, obj):
        return Monetary(obj.total, obj.account.currency)