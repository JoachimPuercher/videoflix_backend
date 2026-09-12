"""Tests for POST /api/password_reset/."""

import re

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.test import APITestCase

from .utils import EMAIL, SYNC_RQ, create_active_user

LINK_PATTERN = re.compile(
    r"confirm_password\.html\?uid=([^&\s]+)&token=([^/\s]+)"
)


@override_settings(RQ_QUEUES=SYNC_RQ)
class PasswordResetTest(APITestCase):
    """A reset request mails a link and never reveals if the address exists."""

    def setUp(self):
        self.url = reverse("password_reset")
        self.user = create_active_user()
        self.message = "An email has been sent to reset your password."

    def test_reset_request(self):
        """A known address is answered with 200 and the spec message."""
        response = self.client.post(self.url, {"email": EMAIL}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": self.message})

    def test_reset_mail_is_sent(self):
        """Exactly one mail goes to the address."""
        self.client.post(self.url, {"email": EMAIL}, format="json")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [EMAIL])

    def test_reset_mail_contains_valid_link(self):
        """The mailed link carries the user id and a token for that user."""
        self.client.post(self.url, {"email": EMAIL}, format="json")
        match = LINK_PATTERN.search(mail.outbox[0].body)
        self.assertIsNotNone(match)
        uidb64, token = match.groups()
        user_id = force_str(urlsafe_base64_decode(uidb64))
        self.assertEqual(user_id, str(self.user.id))
        self.assertTrue(default_token_generator.check_token(self.user, token))

    def test_unknown_email_gets_same_answer_without_mail(self):
        """An unknown address is answered identically, but no mail is sent."""
        known = self.client.post(self.url, {"email": EMAIL}, format="json")
        unknown = self.client.post(
            self.url, {"email": "nobody@example.com"}, format="json"
        )
        self.assertEqual(unknown.status_code, known.status_code)
        self.assertEqual(unknown.data, known.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_email_format(self):
        """A malformed address is answered like any other and sends nothing."""
        response = self.client.post(
            self.url, {"email": "not-an-address"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_email(self):
        """An empty payload sends nothing."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)
