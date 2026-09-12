"""App config for registration, activation, login and password reset."""

from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """No ready() hook: this app registers no signals."""
    name = 'auth_app'
