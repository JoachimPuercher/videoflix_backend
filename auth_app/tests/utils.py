"""Shared helpers for the auth_app tests."""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

# Run rq jobs synchronously inside the test instead of pushing them to the
# real Redis, where the worker would execute them against the development
# database.
SYNC_RQ = {"default": {**settings.RQ_QUEUES["default"], "ASYNC": False}}

# Throttle counters live in the cache. Use an in-memory cache so tests never
# touch the Redis of the running app, and clear it before every test so the
# counters of one test cannot block the next.
LOCAL_CACHE = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

EMAIL = "user@example.com"
PASSWORD = "securepassword"


@override_settings(CACHES=LOCAL_CACHE)
class AuthAPITestCase(APITestCase):
    """APITestCase with an isolated, empty cache per test."""

    def setUp(self):
        super().setUp()
        cache.clear()


def create_active_user(email=EMAIL, password=PASSWORD):
    """Create a user that is allowed to log in."""
    return User.objects.create_user(
        username=email, email=email, password=password
    )


def login(client, email=EMAIL, password=PASSWORD):
    """Log in through the API so the client carries the JWT cookies."""
    return client.post(
        reverse("login"),
        {"email": email, "password": password},
        format="json",
    )
