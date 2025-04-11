# monkey_budget/tokens.py to plik zawierający tokeny używane do aktywacji konta i logowania za pomocą linku

from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for account activation via email
    """
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )


class MagicLinkTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for magic link logins
    """
    def _make_hash_value(self, user, timestamp):
        login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(login_timestamp)
        )


account_activation_token = AccountActivationTokenGenerator()
magic_link_token = MagicLinkTokenGenerator()
password_reset_token = PasswordResetTokenGenerator() 
