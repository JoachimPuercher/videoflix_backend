"""Tests for POST /api/register/."""

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from .utils import SYNC_RQ, AuthAPITestCase


@override_settings(RQ_QUEUES=SYNC_RQ)
class RegisterTest(AuthAPITestCase):
    """Registration creates an inactive user and sends the activation mail."""

    def setUp(self):
        super().setUp()
        self.url = reverse("register")
        self.correct_payload = {
            "email": "user@example.com",
            "password": "securepassword",
            "confirmed_password": "securepassword",
        }
        self.incorrect_email = {
            "email": "userexample.com",
            "password": "securepassword",
            "confirmed_password": "securepassword",
        }
        self.incorrect_password = {
            "email": "user@example.com",
            "password": "securepasswordddd",
            "confirmed_password": "securepassword",
        }
        self.missing_payload_fields = {
            "email": "user@example.com",
            "confirmed_password": "securepassword",
        }

    def test_register_user(self):
        """A valid payload is answered with 201."""
        response = self.client.post(
            self.url, self.correct_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_response_body(self):
        """The body matches the spec: user id and email plus a valid token."""
        response = self.client.post(
            self.url, self.correct_payload, format="json"
        )
        user = User.objects.get(email=self.correct_payload["email"])

        self.assertEqual(set(response.data.keys()), {"user", "token"})
        self.assertEqual(
            response.data["user"], {"id": user.id, "email": user.email}
        )
        self.assertNotIn("password", response.data)
        self.assertNotIn("password", response.data["user"])

        self.assertIsInstance(response.data["token"], str)
        self.assertTrue(
            default_token_generator.check_token(user, response.data["token"])
        )

    def test_activation_mail_is_sent(self):
        """Exactly one activation mail goes to the registered address."""
        self.client.post(self.url, self.correct_payload, format="json")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.correct_payload["email"]])

    def test_write_user_in_model(self):
        """The user is persisted."""
        self.client.post(self.url, self.correct_payload, format="json")
        self.assertEqual(User.objects.count(), 1)

    def test_user_inactive_after_register(self):
        """A new user stays inactive until the mail link is used."""
        self.client.post(self.url, self.correct_payload, format="json")
        user = User.objects.get(email="user@example.com")
        self.assertIs(user.is_active, False)

    def test_email_duplicate(self):
        """An already registered address is rejected without a new user."""
        User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="securepassword",
        )
        response = self.client.post(
            self.url, self.correct_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_email_duplicate_case_insensitive(self):
        """The duplicate check ignores letter case."""
        User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="securepassword",
        )
        payload = {**self.correct_payload, "email": "User@Example.com"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_email(self):
        """A malformed address is rejected."""
        response = self.client.post(
            self.url, self.incorrect_email, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password(self):
        """Passwords that fail AUTH_PASSWORD_VALIDATORS are rejected."""
        for weak in ("12345678", "password1", "short"):
            with self.subTest(password=weak):
                payload = {
                    **self.correct_payload,
                    "password": weak,
                    "confirmed_password": weak,
                }
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )
                self.assertIn("password", response.data)
        self.assertEqual(User.objects.count(), 0)

    def test_passwords_mismatch(self):
        """Different password fields are rejected."""
        response = self.client.post(
            self.url, self.incorrect_password, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_request_keys(self):
        """A payload without the password field is rejected."""
        response = self.client.post(
            self.url, self.missing_payload_fields, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
