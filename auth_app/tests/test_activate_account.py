"""Tests for GET /api/activate/<uidb64>/<token>/."""

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status

from .utils import AuthAPITestCase


def activation_url(uidb64, token):
    return reverse("activate", kwargs={"uidb64": uidb64, "token": token})


class ActivateAccountTest(AuthAPITestCase):
    """The mail link activates exactly the user it was issued for."""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="securepassword",
            is_active=False,
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.id))
        self.token = default_token_generator.make_token(self.user)
        self.url = activation_url(self.uidb64, self.token)

    def get_json(self, url):
        """Call the endpoint the way an API client does."""
        return self.client.get(url, HTTP_ACCEPT="application/json")

    def test_activate_returns_message(self):
        """A valid link is answered with 200 and the spec message."""
        response = self.get_json(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, {"message": "Account successfully activated."}
        )

    def test_user_is_active_after_activation(self):
        """The user flag is persisted."""
        self.get_json(self.url)
        self.user.refresh_from_db()
        self.assertIs(self.user.is_active, True)

    def test_activation_is_idempotent(self):
        """Using the link twice keeps the user active and still answers 200."""
        self.get_json(self.url)
        response = self.get_json(self.url)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(self.user.is_active, True)

    def test_browser_gets_html_page(self):
        """A browser request renders the result template."""
        response = self.client.get(self.url, HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "activation_result.html")
        self.assertContains(response, "Account successfully activated.")

    def test_invalid_token_returns_400(self):
        """A tampered token is rejected and the user stays inactive."""
        response = self.get_json(activation_url(self.uidb64, "abc-def"))
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIs(self.user.is_active, False)

    def test_token_of_other_user_returns_400(self):
        """A token issued for another account does not activate this one."""
        other = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="securepassword",
            is_active=False,
        )
        other_token = default_token_generator.make_token(other)
        response = self.get_json(activation_url(self.uidb64, other_token))
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIs(self.user.is_active, False)

    def test_unknown_user_returns_400(self):
        """An id without a user is rejected like an invalid token."""
        unknown_uid = urlsafe_base64_encode(force_bytes(999))
        response = self.get_json(activation_url(unknown_uid, self.token))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_malformed_uid_returns_400(self):
        """A uid that is not base64 is rejected, not a server error."""
        response = self.get_json(activation_url("not-base64!", self.token))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
