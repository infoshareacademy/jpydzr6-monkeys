from django.urls import path
from . import views

urlpatterns = [
    path('konta/dodaj-konto', views.add_money_account, name='dodaj-konto'),
    path('konta/edytuj-konto/<int:account_id>', views.edit_money_account, name='edytuj-konto'),
    path('konta/usun-konto/<int:account_id>', views.delete_money_account, name='usun-konto'),
    path('konta/<int:account_id>', views.show_money_account, name='pokaz-konto'),
    path('', views.dashboard, name='dashboard'),
    path('transakcje/nowa/', views.transaction_create_view, name='nowa-transakcja'),
    path('transakcje/edytuj/<int:transaction_id>', views.transaction_update_view, name='edytuj-transakcje'),
    path('transakcje/lista/', views.transaction_list, name='lista-transakcji'),
    path('raporty/ogolny', views.general_financial_report, name='raport-ogolny'),
    path('raporty/okresowy', views.periodic_financial_report, name='raport-okresowy'),
    path('raporty/filtry', views.filter_financial_reports, name='raport-filtry'),
]
