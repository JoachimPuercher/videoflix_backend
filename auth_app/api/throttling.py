"""Rate limits for the public auth endpoints.

All auth views run without a logged in user, so every class counts per
client IP (AnonRateThrottle). The rates live in
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] under the scope names below.
"""

from rest_framework.throttling import AnonRateThrottle


class RegisterThrottle(AnonRateThrottle):
    """Every call may create an account and sends a mail."""
    scope = 'register'


class ActivationThrottle(AnonRateThrottle):
    """Guessing activation links must stay slow."""
    scope = 'activate'


class LoginThrottle(AnonRateThrottle):
    """Brute force protection; a human needs only a handful of tries."""
    scope = 'login'


class LogoutThrottle(AnonRateThrottle):
    """Cheap endpoint, limited only against abuse loops."""
    scope = 'logout'


class TokenRefreshThrottle(AnonRateThrottle):
    """Called automatically by the frontend, so the limit is generous."""
    scope = 'token_refresh'


class PasswordResetThrottle(AnonRateThrottle):
    """Every call may send a mail (mail bombing protection)."""
    scope = 'password_reset'


class PasswordConfirmThrottle(AnonRateThrottle):
    """Guessing reset tokens must stay slow."""
    scope = 'password_confirm'
