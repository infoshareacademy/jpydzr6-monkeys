from django.contrib import admin
from .models import MoneyAccount, Transaction, SubTransaction

admin.site.register(MoneyAccount)


class SubTransactionInline(admin.TabularInline):
    model = SubTransaction
    extra = 1


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    inlines = [SubTransactionInline]
    list_display = ['id']
