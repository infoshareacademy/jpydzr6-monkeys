from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import MoneyAccount, Transaction, SubTransaction, UserRegistrationData
from django.template.loader import render_to_string
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from django.utils.formats import number_format
from .forms import *
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
        messages.error(self.request, _('Invalid username or password. Please try again.'))
        return super().form_invalid(form)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
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
            
            messages.success(request, _('Please check your email to activate your account.'))
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
        messages.success(request, _('Your account has been activated! You can now log in.'))
        return redirect('monkey_budget:login')
    else:
        messages.error(request, _('The activation link is invalid or expired.'))
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
                
                messages.success(request, _('We have sent a password reset link to your email.'))
                return redirect('monkey_budget:login')
            except User.DoesNotExist:
                messages.error(request, _('No user found with the given email address.'))
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
                    messages.error(request, _('No active user found with the given email address.'))
                    return redirect('monkey_budget:login')
                
                # Send magic link to all matching users
                current_site = get_current_site(request)
                mail_subject = _('Login link - Monkey Budget')
                
                for user in users:
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = magic_link_token.make_token(user)
                    login_link = f"https://{current_site.domain}/monkey-budget/users/magic-login/{uid}/{token}/"
                    
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
                
                messages.success(request, _('We have sent a login link to your email.'))
                return redirect('monkey_budget:login')
            except Exception as e:
                messages.error(request, _('An error occurred while sending the login link.'))
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
        messages.success(request, _('Welcome, %(first_name)s! You have been successfully logged in.') % {'first_name': user.first_name})
        return redirect('monkey_budget:dashboard')
    else:
        messages.error(request, _('The login link is invalid or expired.'))
        return redirect('monkey_budget:login')

def home(request):
    return render(request, 'home.html')

def team(request):
    return render(request, 'team.html')

def contact(request):
    return render (request, 'contact.html')

@login_required
def dashboard(request):
    all_accounts = MoneyAccount.objects.filter(user_id=request.user.id).order_by('name')
    context = {'accounts': all_accounts}
    return render(request, 'account/dashboard.html', context)

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
            return redirect(f'/monkey-budget/konta/{account.id}')
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
            return redirect(f'/monkey-budget/konta/{chosen_account.id}')
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
        return JsonResponse({'success': True, 'message': _('Account deleted.')})
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
        form = TransactionForm(request.POST)
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
                
            messages.success(request, _('Your profile has been updated!'))
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
        messages.success(request, '{% trans "Your account has been deleted. Thank you for using Monkey Budget." %}')
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
                
                messages.success(request, _('Activation email has been resent. Please check your inbox.'))
                return redirect('monkey_budget:login')
            except User.DoesNotExist:
                messages.error(request, _('No inactive account found with this email address.'))
    else:
        form = ResendActivationForm()
    
    return render(request, 'users/resend_activation.html', {'form': form})    