from django.contrib import admin
from .models import MoneyAccount, Transaction, SubTransaction
from .forms import TransactionForm, SubtransactionFormSet
from .money import Monetary, CurrencyHelper

admin.site.register(MoneyAccount)


# class SubTransactionInlineFormset(BaseInlineFormSet):
#
#     def clean(self):
#         # breakpoint()
#         super().clean()
#
#         if not self.is_valid():
#             raise ValidationError("SubTransaction forms must have been validated")
#
#         if not self.cleaned_data:
#             raise ValidationError('You must supply at least one subtransaction')
#
#         for subtransaction in self.cleaned_data:
#             if not subtransaction:
#                 raise ValidationError('Subtransaction must be filled')


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
    readonly_fields = ['total_display', 'balance_after_transaction_display']

    def total_display(self, obj):
        currency = CurrencyHelper.get_currency_by_its_code(obj.account.currency_code)
        return Monetary(obj.total, currency)

    def balance_after_transaction_display(self, obj):
        currency = CurrencyHelper.get_currency_by_its_code(obj.account.currency_code)
        return Monetary(obj.balance, currency)
