"""Tests for GET /api/video/."""

from django.urls import reverse
from rest_framework import status

from .utils import AuthenticatedMediaTestCase, create_video


class VideoListTest(AuthenticatedMediaTestCase):
    """The list is only available to logged in users and hides file paths."""

    def setUp(self):
        super().setUp()
        self.url = reverse("video_list")
        self.video = create_video(title="First", category="drama")
        create_video(title="Second", category="comedy")

    def test_list(self):
        """A logged in user gets all videos."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_fields(self):
        """Each entry exposes exactly the spec fields."""
        response = self.client.get(self.url)
        entry = next(v for v in response.data if v["id"] == self.video.id)
        self.assertEqual(
            set(entry.keys()),
            {"id", "title", "description", "created_at", "category",
             "thumbnail_url"},
        )
        self.assertEqual(entry["title"], "First")
        self.assertEqual(entry["category"], "drama")
        self.assertEqual(entry["thumbnail_url"], self.video.thumbnail_url)

    def test_list_hides_video_file(self):
        """The internal file name never leaves the server."""
        response = self.client.get(self.url)
        for entry in response.data:
            self.assertNotIn("video_file", entry)

    def test_list_requires_login(self):
        """Without cookies the list is not available."""
        self.client.cookies.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_rejects_invalid_cookie(self):
        """A tampered access cookie is not accepted."""
        self.client.cookies["access_token"] = "not-a-token"
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
