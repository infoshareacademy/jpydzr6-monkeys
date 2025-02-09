from django.contrib import admin
from .models import MoneyAccount, MainCategory, SubCategory

# Register your models here.
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
