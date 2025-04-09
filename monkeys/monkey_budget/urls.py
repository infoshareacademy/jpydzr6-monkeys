from django.urls import path
from django.contrib.auth import views as auth_views
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
    path('transakcje/nowa/', views.transaction_create_view, name='nowa-transakcja'),
    path('transakcje/edytuj/<int:transaction_id>', views.transaction_update_view, name='edytuj-transakcje'),
    path('transakcje/lista/', views.transaction_list, name='lista-transakcji'),
    path('users/login/', views.CustomLoginView.as_view(), name='login'),
    path('users/logout/', auth_views.LogoutView.as_view(template_name='users/logout.html', http_method_names=['get', 'post']), name='logout'),
    path('users/register/', views.register, name='register'),
    path('users/profile/', views.profile, name='profile'),
    path('users/password/', auth_views.PasswordChangeView.as_view(
        template_name='users/password_change.html',
        success_url='/monkey-budget/users/password/done/'), 
        name='password_change'),
    path('users/password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='users/password_change_done.html'), 
        name='password_change_done'),
    path('users/activate/<uidb64>/<token>/', views.activate_account, name='activate'),
    path('users/password-reset/', views.password_reset_request, name='password_reset'),
    path('users/password-reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('users/magic-link/', views.magic_link_request, name='magic_link_request'),
    path('users/magic-login/<uidb64>/<token>/', views.magic_link_login, name='magic_link_login'),
    path('users/delete-account/', views.delete_account, name='delete_account'),
    path('users/resend-activation/', views.resend_activation_email, name='resend_activation'),
]
