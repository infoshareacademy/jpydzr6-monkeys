from django.urls import path
from . import views

urlpatterns = [
    path('konta/dodaj-konto', views.add_money_account, name='dodaj-konto'),
    path('konta/edytuj-konto', views.edit_money_account, name='edytuj-konto'),
    path('konta/usun-konto/<int:account_id>', views.delete_money_account, name='usun-konto'),
    path('konta/<int:account_id>', views.show_money_account, name='pokaz-konto'),
    path('', views.dashboard, name='dashboard'),
    path('transakcje/nowa/', views.transaction_create_or_update, name='nowa-transakcja'),
    path('transakcje/lista/', views.transaction_list, name='lista-transakcji'),
]
