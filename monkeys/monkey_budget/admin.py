from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.transaction import commit
from django.forms import BaseInlineFormSet
from .models import MoneyAccount, Transaction, SubTransaction
from .forms import TransactionForm, SubtransactionFormSet

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
    list_display = ['total', 'transaction_direction', 'account']
    search_fields = ['account']
    list_filter = ['transaction_direction', 'date']
    inlines = [SubTransactionInline]
    readonly_fields = ['total', 'balance_after_transaction']
