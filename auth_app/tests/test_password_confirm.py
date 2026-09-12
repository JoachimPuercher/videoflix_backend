"""Tests for POST /api/password_confirm/<uidb64>/<token>/."""

from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from .utils import PASSWORD, create_active_user

NEW_PASSWORD = "brandnewpassword"


def confirm_url(uidb64, token):
    return reverse(
        "password_reset", kwargs={"uidb64": uidb64, "token": token}
    )


class PasswordConfirmTest(APITestCase):
    """The link from the reset mail sets a new password exactly once."""

    def setUp(self):
        self.user = create_active_user()
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.id))
        self.token = default_token_generator.make_token(self.user)
        self.url = confirm_url(self.uidb64, self.token)
        self.payload = {
            "new_password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD,
        }

    def assert_password_unchanged(self):
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_confirm(self):
        """A valid link and matching passwords are answered with 200."""
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {"detail": "Your Password has been successfully reset."},
        )

    def test_password_is_changed(self):
        """The new password works, the old one does not."""
        self.client.post(self.url, self.payload, format="json")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertFalse(self.user.check_password(PASSWORD))

    def test_link_works_only_once(self):
        """After the change the same token is rejected."""
        self.client.post(self.url, self.payload, format="json")
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_passwords_mismatch(self):
        """Different password fields are rejected and nothing changes."""
        payload = {**self.payload, "confirm_password": "something-else"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assert_password_unchanged()

    def test_missing_field(self):
        """A payload without confirm_password is rejected."""
        response = self.client.post(
            self.url, {"new_password": NEW_PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assert_password_unchanged()

    def test_invalid_token(self):
        """A tampered token is rejected and nothing changes."""
        response = self.client.post(
            confirm_url(self.uidb64, "abc-def"), self.payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assert_password_unchanged()

    def test_token_of_other_user(self):
        """A token issued for another account does not change this one."""
        other = create_active_user(email="other@example.com")
        other_token = default_token_generator.make_token(other)
        response = self.client.post(
            confirm_url(self.uidb64, other_token), self.payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assert_password_unchanged()

    def test_unknown_user(self):
        """An id without a user is rejected like an invalid token."""
        unknown_uid = urlsafe_base64_encode(force_bytes(999))
        response = self.client.post(
            confirm_url(unknown_uid, self.token), self.payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_malformed_uid(self):
        """A uid that is not base64 is rejected, not a server error."""
        response = self.client.post(
            confirm_url("not-base64!", self.token), self.payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
