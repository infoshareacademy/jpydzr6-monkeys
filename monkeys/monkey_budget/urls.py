from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .views.transaction import (
AttachmentAddView, AttachmentDeleteView, AttachmentDownloadView, AttachmentUploadView
)

app_name = 'monkey_budget'

urlpatterns = [
    path('', views.home, name='home'),
    path('team/', views.team, name='team'),
    path('contact/', views.contact, name='contact'),
    path('konta/lista', views.show_accounts_list, name='lista-kont'),
    path('konta/dodaj-konto', views.add_money_account, name='dodaj-konto'),
    path('konta/edytuj-konto/<int:account_id>', views.edit_money_account, name='edytuj-konto'),
    path('konta/usun-konto/<int:account_id>', views.delete_money_account, name='usun-konto'),
    path('konta/<int:account_id>', views.show_money_account, name='pokaz-konto'),
    path('api/account-currency-info/<int:account_id>/', views.get_account_currency_info, name='account-currency-info'),
    path('transaction/create/', views.TransactionCreateView.as_view(), name='transaction-create'),
    path('transaction/<int:pk>/update', views.TransactionUpdateView.as_view(), name='transaction-update'),
    path('transaction/<int:pk>/delete', views.TransactionDeleteView.as_view(), name='transaction-delete'),
    path('transaction/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    path('transaction/list/', views.TransactionListView.as_view(), name='transaction-list'),
    path('raporty/okresowy', views.periodic_financial_report, name='raport-okresowy'),
    path('raporty/ogolny', views.general_financial_report, name='raporty-ogolny'),
    path('users/login/', views.CustomLoginView.as_view(), name='login'),
    path('users/logout/', auth_views.LogoutView.as_view(
        next_page='monkey_budget:home',
        template_name='users/logout.html',
    ), name='logout'),
    path('users/register/', views.register, name='register'),
    path('users/profile/', views.profile, name='profile'),
    path('users/password/', auth_views.PasswordChangeView.as_view(
        template_name='users/password_change.html',
        success_url=reverse_lazy('monkey_budget:password_change_done')),
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
    path('transaction/<int:transaction_id>/add-attachment/', AttachmentAddView.as_view(), name='attachment-add'),
    path('attachment/download/<int:pk>/', AttachmentDownloadView.as_view(), name='attachment-download'),
    path('attachment/<int:pk>/delete/', AttachmentDeleteView.as_view(), name='attachment-delete'),
    path('transaction/attachment-upload/', views.AttachmentUploadView.as_view(), name='attachment-upload'),
]
