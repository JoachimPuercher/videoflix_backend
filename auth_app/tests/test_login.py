"""Tests for POST /api/login/."""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class LoginTest(APITestCase):
    """Login checks e-mail and password and hands out the JWT cookies."""

    def setUp(self):
        self.url = reverse("login")
        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="securepassword",
        )
        self.correct_payload = {
            "email": "user@example.com",
            "password": "securepassword",
        }
        self.unknown_email = {
            "email": "nobody@example.com",
            "password": "securepassword",
        }
        self.missing_field = {
            "email": "user@example.com",
        }
        self.wrong_password = {
            "email": "user@example.com",
            "password": "wrong",
        }

    def test_login(self):
        """Valid credentials are answered with 200."""
        response = self.client.post(
            self.url, self.correct_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_response_body(self):
        """The body carries a message and the user, but no tokens."""
        response = self.client.post(
            self.url, self.correct_payload, format="json"
        )
        self.assertEqual(
            response.data,
            {
                "detail": "Login successful",
                "user": {"id": self.user.id, "username": self.user.email},
            },
        )
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_sets_jwt_cookies(self):
        """Both tokens arrive as HttpOnly, Secure, SameSite=Lax cookies."""
        response = self.client.post(
            self.url, self.correct_payload, format="json"
        )
        for name in ("access_token", "refresh_token"):
            with self.subTest(cookie=name):
                cookie = response.cookies[name]
                self.assertTrue(cookie.value)
                self.assertTrue(cookie["httponly"])
                self.assertTrue(cookie["secure"])
                self.assertEqual(cookie["samesite"], "Lax")

    def test_refresh_cookie_expires_after_one_day(self):
        """The refresh cookie is persistent for 24 hours."""
        response = self.client.post(
            self.url, self.correct_payload, format="json"
        )
        self.assertEqual(response.cookies["refresh_token"]["max-age"], 86400)

    def test_cookies_hold_tokens_for_the_user(self):
        """The cookie values are valid JWTs issued for the logged in user."""
        response = self.client.post(
            self.url, self.correct_payload, format="json"
        )
        access = AccessToken(response.cookies["access_token"].value)
        refresh = RefreshToken(response.cookies["refresh_token"].value)
        # Simple JWT stores the id claim as a string.
        self.assertEqual(str(access["user_id"]), str(self.user.id))
        self.assertEqual(str(refresh["user_id"]), str(self.user.id))

    def test_wrong_password(self):
        """A wrong password is rejected without cookies."""
        response = self.client.post(
            self.url, self.wrong_password, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)

    def test_unknown_email(self):
        """An unknown address is rejected."""
        response = self.client.post(
            self.url, self.unknown_email, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_email_and_wrong_password_look_the_same(self):
        """The error does not reveal whether the address exists."""
        unknown = self.client.post(self.url, self.unknown_email, format="json")
        wrong = self.client.post(self.url, self.wrong_password, format="json")
        self.assertEqual(unknown.status_code, wrong.status_code)
        self.assertEqual(unknown.data, wrong.data)

    def test_missing_password(self):
        """A payload without the password field is rejected."""
        response = self.client.post(
            self.url, self.missing_field, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_user_cannot_login(self):
        """An account that was never activated gets no tokens."""
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post(
            self.url, self.correct_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", response.cookies)
