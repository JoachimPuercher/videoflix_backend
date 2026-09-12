"""Tests for GET /api/video/<movie_id>/<resolution>/index.m3u8."""

from django.urls import reverse
from rest_framework import status

from .utils import AuthenticatedMediaTestCase, create_video

PLAYLIST = (
    b"#EXTM3U\n#EXT-X-VERSION:3\n#EXTINF:10.0,\n000.ts\n#EXT-X-ENDLIST\n"
)
HLS_CONTENT_TYPE = "application/vnd.apple.mpegurl"


def playlist_url(movie_id, resolution):
    return reverse(
        "hls_manifest", kwargs={"movie_id": movie_id, "resolution": resolution}
    )


class HlsPlaylistTest(AuthenticatedMediaTestCase):
    """The playlist is served from MEDIA_ROOT for known videos only."""

    def setUp(self):
        super().setUp()
        self.video = create_video()
        self.write_file(self.video.get_path("480p"), PLAYLIST)
        self.url = playlist_url(self.video.id, "480p")

    def test_playlist(self):
        """An existing playlist is delivered as HLS manifest."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], HLS_CONTENT_TYPE)
        self.assertEqual(b"".join(response.streaming_content), PLAYLIST)

    def test_playlist_requires_login(self):
        """Without cookies the manifest is not available."""
        self.client.cookies.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_video(self):
        """An id without a video is a 404."""
        response = self.client.get(playlist_url(999, "480p"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_resolution(self):
        """A resolution outside the whitelist is a 404, not a file lookup."""
        response = self.client.get(playlist_url(self.video.id, "4k"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_playlist_file(self):
        """A valid resolution that was not rendered yet is a 404."""
        response = self.client.get(playlist_url(self.video.id, "720p"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
