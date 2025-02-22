from django.contrib import admin
from .models import MoneyAccount, Transaction, SubTransaction
from .forms import TransactionForm, SubtransactionFormSet
from .money import Monetary, CurrencyHelper

admin.site.register(MoneyAccount)


class SubTransactionInline(admin.TabularInline):
    model = SubTransaction
    formset = SubtransactionFormSet
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
        currency = CurrencyHelper.get_currency_by_its_code(obj.account.currency_code)
        return Monetary(obj.total, currency)
