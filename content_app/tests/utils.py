"""Shared helpers for the content_app tests."""

import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from content_app.models import Video

EMAIL = "user@example.com"
PASSWORD = "securepassword"


def create_video(**fields):
    """Create a video without triggering the ffmpeg jobs of the signal."""
    data = {
        "title": "Test video",
        "description": "A video for tests",
        "category": "test",
        "thumbnail_url": "http://example.com/thumb.jpg",
        "video_file": "test.mp4",
    }
    data.update(fields)
    with patch("content_app.signals.django_rq.get_queue"):
        return Video.objects.create(**data)


class AuthenticatedMediaTestCase(APITestCase):
    """Logged in client plus a throwaway MEDIA_ROOT for generated files."""

    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        override = override_settings(MEDIA_ROOT=self.media_root)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)

        self.user = User.objects.create_user(
            username=EMAIL, email=EMAIL, password=PASSWORD
        )
        self.client.post(
            reverse("login"),
            {"email": EMAIL, "password": PASSWORD},
            format="json",
        )

    def write_file(self, path, content: bytes):
        """Create the file at path, including its parent folders."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
