from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, Value
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.functions import Coalesce
from .models import MoneyAccount, Transaction, SubTransaction, UserRegistrationData
from django.template.loader import render_to_string
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from django.utils.formats import number_format
from .forms import *
from .money import CurrencyHelper, currencies
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from .tokens import account_activation_token, magic_link_token, password_reset_token
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from ipware import get_client_ip
from django.utils.translation import gettext as _


class CustomLoginView(LoginView):
    template_name = 'users/login.html'

    def form_invalid(self, form):
        """If the form is invalid, render the invalid form with custom error messages."""
        messages.error(self.request, _('Nieprawidłowa nazwa użytkownika lub hasło. Proszę spróbować ponownie.'))
        return super().form_invalid(form)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Check if username or email already exists
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            if User.objects.filter(username=username).exists():
                form.add_error('username', _('Użytkownik o tej nazwie już istnieje.'))
                return render(request, 'users/register.html', {'form': form})

            if User.objects.filter(email=email).exists():
                form.add_error('email', _('Konto z tym adresem email już istnieje.'))
                return render(request, 'users/register.html', {'form': form})

            user = form.save()

            # Get IP address using django-ipware
            ip, is_routable = get_client_ip(request)

            # Create registration data with IP and user agent
            UserRegistrationData.objects.create(
                user=user,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            # Generate activation token
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)

            # Create activation link
            activation_url = request.build_absolute_uri(
                reverse('monkey_budget:activate', args=[uid, token])
            )

            # Send activation email
            try:
                subject = _('Activate your account')
                message = render_to_string('users/email/account_activation_email.html', {
                    'user': user,
                    'activation_url': activation_url,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                    'domain': request.get_host(),
                })

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=message,
                    fail_silently=False,
                )
                messages.success(request, _('Proszę sprawdzić swoją skrzynkę odbiorczą w celu aktywacji konta.'))
            except Exception as e:
                # Log the error (you might want to add proper logging here)
                print(f"Error sending email: {e}")
                # Set user as active since we couldn't send activation email
                user.is_active = True
                user.save()
                messages.warning(request, _('Konto zostało utworzone, ale wystąpił problem z wysłaniem emaila aktywacyjnego. Możesz się teraz zalogować.'))

            return redirect('monkey_budget:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def activate_account(request, uidb64, token):
    """View for activating a user account via email link"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, _('Twoje konto zostało aktywowane! Możesz teraz się zalogować.'))
        return redirect('monkey_budget:login')
    else:
        messages.error(request, _('Link do aktywacji konta jest nieprawidłowy lub wygasł.'))
        return redirect('monkey_budget:login')

def password_reset_request(request):
    """View for requesting a password reset via email"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)

                # Create password reset link
                current_site = get_current_site(request)
                mail_subject = _('Password reset - Monkey Budget')
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = password_reset_token.make_token(user)
                reset_link = f"https://{current_site.domain}/monkey-budget/users/password-reset/{uid}/{token}/"

                # Render email template
                message = render_to_string('users/email/password_reset_email.html', {
                    'user': user,
                    'reset_url': reset_link,
                })

                # Send email
                send_mail(
                    mail_subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=message,
                    fail_silently=False
                )

                messages.success(request, _('Wysłano link do zresetowania hasła na podany adres email.'))
                return redirect('monkey_budget:login')
            except User.DoesNotExist:
                messages.error(request, _('Nie znaleziono użytkownika z podanym adresem email.'))
    else:
        form = PasswordResetRequestForm()

    return render(request, 'users/password_reset_request.html', {'form': form})

def password_reset_confirm(request, uidb64, token):
    """View for setting a new password after reset request"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and password_reset_token.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                messages.success(request, 'Hasło zostało zmienione! Możesz się teraz zalogować.')
                return redirect('monkey_budget:login')
        else:
            form = SetPasswordForm()

        return render(request, 'users/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'Link do resetowania hasła jest nieprawidłowy lub wygasł.')
        return redirect('monkey_budget:login')

def magic_link_request(request):
    """View for requesting a magic login link via email"""
    if request.method == 'POST':
        form = MagicLinkLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                # Get all active users with this email
                users = User.objects.filter(email=email, is_active=True)

                if not users.exists():
                    messages.error(request, _('Nie znaleziono aktywnego użytkownika z podanym adresem email.'))
                    return redirect('monkey_budget:login')

                # Send magic link to all matching users
                current_site = get_current_site(request)
                mail_subject = _('Login link - Monkey Budget')

                for user in users:
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = magic_link_token.make_token(user)
                    login_link = f"https://{current_site.domain}/users/magic-login/{uid}/{token}/"

                    # Render email template
                    message = render_to_string('users/email/magic_link_email.html', {
                        'user': user,
                        'login_url': login_link,
                    })

                    # Send email
                    send_mail(
                        mail_subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=message,
                        fail_silently=False
                    )

                messages.success(request, _('Wysłano link do logowania na podany adres email.'))
                return redirect('monkey_budget:login')
            except Exception as e:
                messages.error(request, _('Wystąpił błąd podczas wysyłania linku do logowania.'))
                return redirect('monkey_budget:login')
    else:
        form = MagicLinkLoginForm()

    return render(request, 'users/magic_link_request.html', {'form': form})

def magic_link_login(request, uidb64, token):
    """View for logging in via magic link"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and magic_link_token.check_token(user, token):
        login(request, user)
        messages.success(request, _('Witaj, %(first_name)s! Zostałeś pomyślnie zalogowany.') % {'first_name': user.first_name})
        return redirect('monkey_budget:lista-transakcji')
    else:
        messages.error(request, _('Link do logowania jest nieprawidłowy lub wygasł.'))
        return redirect('monkey_budget:login')

def home(request):
    return render(request, 'home.html')

def team(request):
    return render(request, 'team.html')

def contact(request):
    return render (request, 'contact.html')

@login_required
def show_accounts_list(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    context = {'accounts': all_accounts}
    return render(request, 'account/show_accounts_list.html', context)
@login_required
def show_money_account(request, account_id):
    account_related_transactions = Transaction.objects.filter(account_id=account_id).order_by('-date')
    transactions_context = {'transactions': account_related_transactions}
    transactions_list_html = render_to_string('account/transactions_list_for_include.html', transactions_context)
    chosen_account = get_object_or_404(MoneyAccount, pk=account_id, user_id=request.user.id)
    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id).order_by('name')
    context = {'account': chosen_account, 'accounts': all_accounts, 'transactions_list_html': transactions_list_html}
    return render(request, 'account/show_account.html', context)

@login_required
def add_money_account(request):
    if request.method == 'POST':
        form = MoneyAccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user_id = request.user
            account.balance = Monetary.major_to_minor_unit(form.cleaned_data['balance'], account.currency)
            account.save()
            return redirect(f'/konta/{account.id}')
    else:
        form = MoneyAccountForm()
    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id).order_by('name')
    return render(request, 'account/add_account.html', {'form': form, 'accounts': all_accounts})

@login_required
def edit_money_account(request, account_id):
    chosen_account = get_object_or_404(MoneyAccount, pk=account_id, user_id=request.user.id)
    if request.method == 'POST':
        form = MoneyAccountForm(request.POST, instance=chosen_account)
        if form.is_valid():
            account = form.save(commit=False)
            account.balance = Monetary.major_to_minor_unit(form.cleaned_data['balance'], account.currency)
            form.save()
            return redirect(f'/konta/{chosen_account.id}')
    else:
        initial_data = {
            'balance': Monetary(chosen_account.balance, chosen_account.currency).amount_as_decimal
        }
        form = MoneyAccountForm(instance=chosen_account, initial=initial_data)

    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id).order_by('name')
    context = {'account': chosen_account, 'accounts': all_accounts, 'form': form}
    return render(request, 'account/edit_account.html', context)

@login_required
def delete_money_account(request, account_id):
    if request.method == 'POST':
        account = get_object_or_404(MoneyAccount, id=account_id, user_id=request.user.id)
        account.delete()
        return JsonResponse({'success': True, 'message': _('Konto zostało usunięte.')})
    return JsonResponse({'success': False, 'message': _('Invalid request.')})

@api_view(['GET'])
# TODO: Kiedy użytkownik zostanie zaimplementowany, odkomentować linię z @permission classes. Niewykluczone, że będzie
#  potrzebny też dopuszczenie metody autentykacji przez sesję, wtedy nalezy dodać @authentication_classes([SessionAuthentication
#  Ponadto odkomentować blok warunkowy `if account.user_id != request.user:`
@permission_classes([IsAuthenticated])
def get_account_currency_info(request, account_id):
    try:
        account = MoneyAccount.objects.get(pk=account_id)
        # if account.user_id != request.user:
        #     # Zabezpieczenie przed odpytywaniem api bez zalogowanego użytkownika
        #     raise PermissionDenied(detail="You must be logged in to request this data")
        currency = account.currency
        step = f"0.{'0' * (currency['exponent']-1)}1" if currency['exponent'] > 0 else "1"
        placeholder = f"0.{'0' * (currency['exponent'])}" if currency['exponent'] > 0 else "0"
        placeholder = Decimal(placeholder)
        placeholder = number_format(placeholder, decimal_pos=currency['exponent'])
        return Response({
            'step': step,
            'placeholder': placeholder,
        })
    except MoneyAccount.DoesNotExist:
        raise NotFound(detail='Money account not found')


@login_required
def transaction_create_view(request):
    header = 'Nowa transakcja'
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            formset = SubTransactionFormSet(
                request.POST,
                form_kwargs={
                    'main_transaction_account': form.cleaned_data.get('account'),
                }
            )
            if formset.is_valid():
                with transaction.atomic():
                    transaction_form = form.save()
                    formset.instance = transaction_form
                    formset.save()
                    return redirect('monkey_budget:lista-transakcji')
            else:
                for error in formset.non_form_errors():
                    messages.error(request, error)
        else:
            formset = SubTransactionFormSet(request.POST)
    else:
        form = TransactionForm()
        formset = SubTransactionFormSet()
    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id).order_by('name')
    context = {
        'header': header,
        'form': form,
        'formset': formset,
        'accounts': all_accounts,
    }
    return render(request, 'account/transaction_form.html', context)


@login_required
def transaction_update_view(request, transaction_id):
    header = 'Edycja transakcji'
    # Make sure the transaction belongs to an account owned by the current user
    obj = get_object_or_404(Transaction, id=transaction_id, account__user_id=request.user.id)
    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id).order_by('name')
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=obj, user=request.user)
        formset = SubTransactionFormSet(request.POST, instance=obj)
        formset.extra = 0
        context = {
            'header': header,
            'form': form,
            'formset': formset,
            'accounts': all_accounts,
        }
        if all([form.is_valid(), formset.is_valid()]):
            with transaction.atomic():
                transaction_form = form.save()
                formset.instance = transaction_form
                formset.save()
            messages.success(request, 'Edycja transakcji udana!')
            return redirect('monkey_budget:edytuj-transakcje', transaction_id)
        else:
            for error in formset.non_form_errors():
                messages.error(request, error)
    else:
        form = TransactionForm(instance=obj, user=request.user)
        formset = SubTransactionFormSet(instance=obj)
        formset.extra = 0
        context = {
            'header': header,
            'form': form,
            'formset': formset,
            'accounts': all_accounts,
        }
    return render(request, 'account/transaction_form.html', context)


@login_required
def transaction_list(request):
    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id)
    # Get transactions linked to accounts owned by the current user
    transactions = Transaction.objects.filter(account__user_id=request.user.id)
    return render(request, 'account/transactions_list.html', {
        'transactions': transactions,
        'accounts': all_accounts,
    })

def general_financial_report(request):
    all_accounts = MoneyAccount.objects.filter(user_id=2).order_by('name')
    all_currencies_balance = []
    account_balances = []

    for currency in currencies.__all__:
        chosen_accounts = all_accounts.filter(currency_code=currency)
        currency_balance = sum(account.balance for account in chosen_accounts)
        decimal_currency_balance = Monetary(currency_balance, CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal
        all_currencies_balance.append((currency,decimal_currency_balance))

    for account_type in MoneyAccount.types:
        type_code = account_type[0]
        type_name = account_type[1].capitalize()
        type_data = {
            'type_name': type_name,
            'currency_balances': []
        }

        for currency in currencies.__all__:
            accounts = all_accounts.filter(type=type_code, currency_code=currency)
            total_balance = sum(account.balance for account in accounts)
            type_data['currency_balances'].append((
                    Monetary(total_balance, CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal,
                    currency
                ))

        account_balances.append(type_data)

    context = {
        'accounts': all_accounts,
        'all_currencies_balance': all_currencies_balance,
        'account_balances': account_balances,
    }
    return render(request, 'account/general_financial_report.html', context)



@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # Save the user form
            form.save()

            # Handle avatar upload if provided
            if 'avatar' in request.FILES:
                request.user.profile.avatar = request.FILES['avatar']
                request.user.profile.save()

            messages.success(request, _('Twoje konto zostało zaktualizowane!'))
            return redirect('monkey_budget:profile')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'users/profile.html', {'form': form})

@login_required
def delete_account(request):
    """View for deleting a user account"""
    if request.method == 'POST':
        # Delete user's accounts and transactions first
        user = request.user
        MoneyAccount.objects.filter(user_id=user.id).delete()

        # Now delete the user
        user.delete()
        messages.success(request, _('Twoje konto zostało usunięte. Dziękujemy za używanie Monkey Budget.'))
        return redirect('monkey_budget:login')

    return render(request, 'users/delete_account.html')

def resend_activation_email(request):
    """View for resending account activation email"""
    if request.method == 'POST':
        form = ResendActivationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email, is_active=False)

                # Generate activation token
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = account_activation_token.make_token(user)

                # Create activation link
                activation_url = request.build_absolute_uri(
                    reverse('monkey_budget:activate', args=[uid, token])
                )

                # Send activation email
                subject = _('Activate your account')
                message = render_to_string('users/email/account_activation_email.html', {
                    'user': user,
                    'activation_url': activation_url,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                    'domain': request.get_host(),
                })

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=message,
                    fail_silently=False,
                )

                messages.success(request, _('Email aktywacyjny został wysłany ponownie. Proszę sprawdzić swoją skrzynkę odbiorczą.'))
                return redirect('monkey_budget:login')
            except User.DoesNotExist:
                messages.error(request, _('Nie znaleziono nieaktywnego konta z tym adresem email.'))
    else:
        form = ResendActivationForm()

    return render(request, 'users/resend_activation.html', {'form': form})



def periodic_financial_report(request):
    all_accounts = MoneyAccount.objects.filter(user_id=4).order_by('name')
    start_date = (date.today() - timedelta(days=30))
    end_date = (date.today())
    currency_incomes_outcomes_balance = {'balances':[]}
    date_filtered_transactions = None

    if request.method == 'POST':
        form = PeriodicFinancialReport(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            extended_end_date = end_date + timedelta(days=1)
            date_filtered_transactions = Transaction.objects.filter(
                account__user_id=4,
                date__range=(start_date, extended_end_date)
            )

            # todo nie można brać aktualnego balansu konta - jest brany też dla okresów kiedy konto nie istniało,
            #  lepiej brać saldo z ostatniej transakcji na danym koncie
            # todo obsłuż sytuację, że dla danego okresu nie ma danych do wyświetlenia
            for currency in currencies.__all__:
                currency_balance_after_period = []
                all_accounts_currency_filtered = all_accounts.filter(currency_code=currency)
                if all_accounts_currency_filtered:
                    for account in all_accounts.filter(currency_code=currency):
                        ordered_transactions = date_filtered_transactions.filter(account_id=account.id).order_by('-date')
                        if ordered_transactions:
                            end_period_account_balance = ordered_transactions[0].balance_after_transaction
                        else:
                            end_period_account_balance = account.balance
                        currency_balance_after_period.append(end_period_account_balance)
                    balance_after_period = sum(currency_balance_after_period)

                    incomes_total = date_filtered_transactions.filter(
                        account__currency_code= currency,
                        transaction_direction='IN'
                    ).aggregate(total_sum=Coalesce(Sum('total'), Value(0)))

                    outcomes_total = date_filtered_transactions.filter(
                        account__currency_code= currency,
                        transaction_direction='OUT'
                    ).aggregate(total_sum=Coalesce(Sum('total'), Value(0)))
                    income_outcome_balance = incomes_total['total_sum'] - outcomes_total['total_sum']

                    currency_incomes_outcomes_balance['balances'].append({
                            'currency_code': currency,
                            'incomes_total': Monetary(incomes_total['total_sum'], CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal,
                            'outcomes_total': Monetary(outcomes_total['total_sum'], CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal,
                            'income_outcome_balance': Monetary(income_outcome_balance, CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal,
                            'balance_after_period': Monetary(balance_after_period, CurrencyHelper.get_currency_by_its_code(currency)).amount_as_decimal,
                        })
    else:
        form = PeriodicFinancialReport()

    context = {
        'accounts': all_accounts,
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'currency_incomes_outcomes_balance': currency_incomes_outcomes_balance,
        'date_filtered_transactions': date_filtered_transactions,
    }
    return render(request, 'account/periodic_financial_report.html', context)
