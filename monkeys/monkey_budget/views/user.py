from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from ..models import MoneyAccount, Transaction, SubTransaction, UserRegistrationData
from django.contrib import messages
from ..forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from ..tokens import account_activation_token, magic_link_token, password_reset_token
from django.conf import settings
from django.urls import reverse
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
        return redirect('monkey_budget:transaction-list')
    else:
        messages.error(request, _('Link do logowania jest nieprawidłowy lub wygasł.'))
        return redirect('monkey_budget:login')


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