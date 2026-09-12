"""JWT authentication that reads the access token from an HttpOnly cookie.

Simple JWT expects the token in the Authorization header; this project sends
it as a cookie so JavaScript can never read it. The class is the default in
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"].
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from typing import Optional

from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request


from rest_framework_simplejwt.tokens import Token, AuthUser


class JWTCookieAuthentication(JWTAuthentication):
    """Authenticate with the access_token cookie instead of a header."""

    def authenticate(
            self, request: Request) -> Optional[tuple[AuthUser, Token]]:
        """Return (user, token) for a valid cookie, None if no cookie is sent.

        An invalid or expired token raises InvalidToken (401) through
        get_validated_token, exactly like the header based parent class.
        """
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        return self.get_user(validated_token), validated_token


class JWTCookieRefreshAuthentication(JWTAuthentication):
    """Unused copy of JWTCookieAuthentication, kept for a refresh flow."""

    def authenticate(
            self, request: Request) -> Optional[tuple[AuthUser, Token]]:
        """Same as JWTCookieAuthentication.authenticate."""
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        return self.get_user(validated_token), validated_token
