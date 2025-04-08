from django.urls import path
from . import views


app_name = 'monkey_budget'

urlpatterns = [
    path('', views.home, name='home'),
    path('team/', views.team, name='team'),
    path('contact/', views.contact, name='contact'),
    path('konta/dodaj-konto', views.add_money_account, name='dodaj-konto'),
    path('konta/edytuj-konto/<int:account_id>', views.edit_money_account, name='edytuj-konto'),
    path('konta/usun-konto/<int:account_id>', views.delete_money_account, name='usun-konto'),
    path('konta/<int:account_id>', views.show_money_account, name='pokaz-konto'),
    path('konta/dasboard/', views.dashboard, name='dashboard'),
    path('api/account-currency-info/<int:account_id>', views.get_account_currency_info, name='account-currency-info'),
path('transaction/create/', views.TransactionCreateView.as_view(), name='transaction-create'),
    path('transaction/<int:pk>/update', views.TransactionUpdateView.as_view(), name='transaction-update'),
    path('transakcje/lista/', views.transaction_list, name='lista-transakcji'),
]
