"""Tests for POST /api/logout/."""

from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from .utils import AuthAPITestCase, create_active_user, login


class LogoutTest(AuthAPITestCase):
    """Logout blacklists the refresh token and removes both cookies."""

    def setUp(self):
        super().setUp()
        self.url = reverse("logout")
        self.user = create_active_user()
        login(self.client)
        self.refresh_token = self.client.cookies["refresh_token"].value

    def assert_cookies_deleted(self, response):
        """Both JWT cookies are sent back expired."""
        for name in ("access_token", "refresh_token"):
            with self.subTest(cookie=name):
                self.assertEqual(response.cookies[name].value, "")
                self.assertEqual(response.cookies[name]["max-age"], 0)

    def test_logout(self):
        """A logged in user is answered with 200."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_deletes_cookies(self):
        """The response expires both JWT cookies."""
        response = self.client.post(self.url)
        self.assert_cookies_deleted(response)

    def test_logout_blacklists_refresh_token(self):
        """The refresh token is stored in the blacklist."""
        self.client.post(self.url)
        self.assertEqual(BlacklistedToken.objects.count(), 1)

    def test_old_refresh_token_is_rejected_after_logout(self):
        """The refresh token from before the logout can not be used again."""
        self.client.post(self.url)
        self.client.cookies["refresh_token"] = self.refresh_token
        response = self.client.post(reverse("token_refresh"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_token_still_deletes_cookies(self):
        """A broken refresh cookie is answered with 200 and cleared."""
        self.client.cookies["refresh_token"] = "not-a-token"
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_cookies_deleted(response)

    def test_logout_twice(self):
        """A second logout with the same token is harmless."""
        self.client.post(self.url)
        self.client.cookies["refresh_token"] = self.refresh_token
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_cookies_deleted(response)

    def test_logout_without_cookie(self):
        """Without a refresh cookie there is nothing to blacklist."""
        self.client.cookies.clear()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(BlacklistedToken.objects.count(), 0)
