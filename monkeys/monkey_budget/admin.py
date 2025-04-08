from django.contrib import admin

from .models import MoneyAccount, Transaction, SubTransaction, MainCategory, SubCategory
from .forms import TransactionForm, SubTransactionFormSet, SubTransactionForm
from .money import Monetary

admin.site.register(MoneyAccount)

class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1

@admin.register(MainCategory)
class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_id', 'category_type')
    list_filter = ('category_type', 'user_id')
    search_fields = ('name', 'description')
    inlines = [SubCategoryInline]

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category')
    list_filter = ('parent_category',)
    search_fields = ('name', 'description')


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

    def get_formset_kwargs(self, request, obj, inline, prefix):
        if request.method == 'POST':
            account_id = request.POST.get('account')
            account = MoneyAccount.objects.get(pk=account_id)
            return {
                **super().get_formset_kwargs(request, obj, inline, prefix),
                "form_kwargs": {"main_transaction_account": account}
            }
        else:
            return{
                **super().get_formset_kwargs(request, obj, inline, prefix),
            }

    def total_display(self, obj):
        return Monetary(obj.total, obj.account.currency)