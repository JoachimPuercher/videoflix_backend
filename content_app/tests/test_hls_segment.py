"""Tests for GET /api/video/<movie_id>/<resolution>/<segment>/."""

from pathlib import Path

from django.urls import reverse
from rest_framework import status

from .utils import AuthenticatedMediaTestCase, create_video

SEGMENT = b"\x47" * 188 * 3  # three fake MPEG-TS packets


def segment_url(movie_id, resolution, segment):
    return reverse(
        "hls_segment",
        kwargs={"movie_id": movie_id, "resolution": resolution,
                "segment": segment},
    )


class HlsSegmentTest(AuthenticatedMediaTestCase):
    """Segments are served from the resolution folder of the video only."""

    def setUp(self):
        super().setUp()
        self.video = create_video()
        self.write_file(self.video.get_segment("480p", "000.ts"), SEGMENT)
        self.url = segment_url(self.video.id, "480p", "000.ts")

    def test_segment(self):
        """An existing segment is delivered as MPEG-TS."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "video/MP2T")
        self.assertEqual(b"".join(response.streaming_content), SEGMENT)

    def test_segment_requires_login(self):
        """Without cookies the segment is not available."""
        self.client.cookies.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_video(self):
        """An id without a video is a 404."""
        response = self.client.get(segment_url(999, "480p", "000.ts"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_resolution(self):
        """A resolution outside the whitelist is a 404."""
        response = self.client.get(
            segment_url(self.video.id, "4k", "000.ts")
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_segment(self):
        """A segment that does not exist is a 404."""
        response = self.client.get(
            segment_url(self.video.id, "480p", "001.ts")
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_segment_of_other_video_is_not_reachable(self):
        """Segments are looked up per video, not globally."""
        other = create_video(title="Other")
        response = self.client.get(segment_url(other.id, "480p", "000.ts"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_path_traversal_is_rejected(self):
        """A segment name that climbs out of the folder reaches no file."""
        secret = Path(self.media_root) / "videos" / "secret.txt"
        self.write_file(secret, b"top secret")
        path = (
            f"/api/video/{self.video.id}/480p/..%2F..%2Fsecret.txt/"
        )
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
