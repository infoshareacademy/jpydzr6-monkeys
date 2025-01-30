from django.urls import path
from . import views

urlpatterns = [
    path('konta', views.money_accounts, name='konta'),
    path('konta/dodaj-konto', views.add_money_account, name='dodaj-konto'),
    path('konta/edytuj-konto', views.edit_money_account, name='edytuj-konto'),
    path('konta/usun-konto', views.delete_money_account, name='usun-konto'),
    path('konta/pokaz-konto', views.show_money_account, name='pokaz-konto'),
]
