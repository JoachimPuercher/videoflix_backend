"""Shared helpers for the auth_app tests."""

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

# Run rq jobs synchronously inside the test instead of pushing them to the
# real Redis, where the worker would execute them against the development
# database.
SYNC_RQ = {"default": {**settings.RQ_QUEUES["default"], "ASYNC": False}}

EMAIL = "user@example.com"
PASSWORD = "securepassword"


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
