"""Video model plus the file layout of its rendered HLS output.

Everything derived from an upload lives under
MEDIA_ROOT/videos/<id>/: one folder per resolution with index.m3u8 and the
.ts segments, and thumbnail.jpg next to them. A thumbnail uploaded in the
admin is stored re-encoded under MEDIA_ROOT/thumbnails/ instead.
"""

import os
from django.db import models
from pathlib import Path
from django.conf import settings
from django.urls import reverse

from content_app.images import validate_thumbnail_image


class Video(models.Model):
    """An uploaded video; the worker renders the HLS variants after save."""

    class Resolution(models.TextChoices):
        """Rendered resolutions; also the whitelist for URL parameters."""
        P480 = "480p"
        P720 = "720p"
        P1080 = "1080p"

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    # Left blank on upload: filled after save, for an uploaded thumbnail
    # right away, otherwise by the worker once the frame is grabbed.
    thumbnail_url = models.URLField(max_length=200, blank=True)
    # Optional; if empty, the worker grabs a frame from the video instead.
    thumbnail_file = models.FileField(
        blank=True,
        upload_to="thumbnails/",
        validators=[validate_thumbnail_image],
    )
    category = models.CharField(max_length=40)
    video_file = models.FileField()

    def __str__(self):
        return self.title

    def get_path(self, resolution: "Video.Resolution") -> Path:
        """Path of the HLS playlist for one resolution (may not exist yet)."""
        video_path = Path(settings.MEDIA_ROOT) / "videos" / \
            str(self.id) / resolution
        playlist = video_path / "index.m3u8"
        return playlist

    def get_segment(
            self,
            resolution: "Video.Resolution",
            url_segment: str) -> Path:
        """Path of one .ts segment; the caller validates url_segment."""
        video_path = Path(settings.MEDIA_ROOT) / "videos" / \
            str(self.id) / resolution
        segment = video_path / url_segment
        return segment

    def get_thumbnail_path(self) -> Path:
        """Path of the generated preview image."""
        return Path(settings.MEDIA_ROOT) / "videos" / \
            str(self.id) / "thumbnail.jpg"

    def get_thumbnail_url(self) -> str:
        """Absolute URL of the public thumbnail endpoint of this video."""
        # reverse() follows urls.py, BACKEND_URL adds scheme and host.
        path = reverse("video_thumbnail", kwargs={"movie_id": self.id})
        return f"{os.getenv('BACKEND_URL')}{path}"
