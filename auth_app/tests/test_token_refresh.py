"""Tests for POST /api/token/refresh/."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .utils import create_active_user, login


class TokenRefreshTest(APITestCase):
    """The refresh cookie yields a new access cookie."""

    def setUp(self):
        self.url = reverse("token_refresh")
        self.user = create_active_user()
        login(self.client)
        self.old_access = self.client.cookies["access_token"].value

    def test_refresh(self):
        """A valid refresh cookie is answered with 200."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_response_body(self):
        """The body confirms the refresh and does not echo the token."""
        response = self.client.post(self.url)
        self.assertEqual(response.data["detail"], "Token refreshed.")
        self.assertNotEqual(
            response.data.get("access"),
            response.cookies["access_token"].value,
        )

    def test_refresh_sets_new_access_cookie(self):
        """A fresh HttpOnly access cookie replaces the old one."""
        response = self.client.post(self.url)
        cookie = response.cookies["access_token"]
        self.assertNotEqual(cookie.value, self.old_access)
        self.assertTrue(cookie["httponly"])
        self.assertTrue(cookie["secure"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_new_access_token_belongs_to_user(self):
        """The new token carries the id of the logged in user."""
        response = self.client.post(self.url)
        token = AccessToken(response.cookies["access_token"].value)
        self.assertEqual(str(token["user_id"]), str(self.user.id))

    def test_refresh_keeps_refresh_cookie(self):
        """Without rotation the refresh cookie is not reissued."""
        response = self.client.post(self.url)
        self.assertNotIn("refresh_token", response.cookies)

    def test_new_access_token_grants_access(self):
        """A protected endpoint accepts the refreshed cookie."""
        self.client.post(self.url)
        response = self.client.get(reverse("video_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_without_cookie(self):
        """A missing refresh cookie is a bad request."""
        self.client.cookies.clear()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_with_invalid_cookie(self):
        """A broken refresh cookie is rejected and both cookies are cleared."""
        self.client.cookies["refresh_token"] = "not-a-token"
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_access_token_is_not_accepted_as_refresh_token(self):
        """The short lived access token can not be used to refresh."""
        self.client.cookies["refresh_token"] = self.old_access
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
