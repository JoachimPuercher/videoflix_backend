"""Tests for GET /api/video/<movie_id>/thumbnail.jpg."""

from django.urls import reverse
from rest_framework import status

from .utils import AuthenticatedMediaTestCase, create_video

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64 + b"\xff\xd9"  # minimal JPEG bytes


def thumbnail_url(movie_id):
    return reverse("video_thumbnail", kwargs={"movie_id": movie_id})


class VideoThumbnailTest(AuthenticatedMediaTestCase):
    """Thumbnails are public images served by the API for <img> tags."""

    def setUp(self):
        super().setUp()
        self.video = create_video()
        self.write_file(self.video.get_thumbnail_path(), JPEG)
        self.url = thumbnail_url(self.video.id)

    def test_thumbnail(self):
        """An existing thumbnail is delivered as JPEG."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertEqual(b"".join(response.streaming_content), JPEG)

    def test_thumbnail_is_cacheable(self):
        """Browsers and proxies may keep the image for a day."""
        response = self.client.get(self.url)
        self.assertEqual(response["Cache-Control"], "public, max-age=86400")

    def test_thumbnail_without_login(self):
        """An <img> tag sends no cookie, so the image must not need one."""
        self.client.cookies.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_thumbnail_ignores_broken_cookie(self):
        """A stale access cookie must not turn the image into a 401."""
        self.client.cookies["access_token"] = "not-a-token"
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unknown_video(self):
        """An id without a video is a 404."""
        response = self.client.get(thumbnail_url(999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_file(self):
        """A video whose thumbnail was not generated yet is a 404."""
        other = create_video(title="No thumbnail yet")
        response = self.client.get(thumbnail_url(other.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
