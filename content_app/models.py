from django.db import models
from pathlib import Path
from django.conf import settings

# Create your models here.

class Video(models.Model):

    class Resolution(models.TextChoices):
        """Resolutions the worker renders; also the whitelist for URL parameters."""
        P480 = "480p"
        P720 = "720p"
        P1080 = "1080p"

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    # Left blank on upload: the worker fills it with the generated thumbnail.
    thumbnail_url = models.URLField(max_length=200, blank=True)
    category = models.CharField(max_length=40)
    video_file = models.FileField()

    def __str__(self):
        return self.title

    def get_path(self, resolution: "Video.Resolution") -> Path:
        video_path = Path(settings.MEDIA_ROOT) / "videos" / str(self.id) / resolution 
        playlist = video_path / "index.m3u8"
        return playlist

    def get_segment(self, resolution: "Video.Resolution", url_segment:str) -> Path:
        video_path = Path(settings.MEDIA_ROOT) / "videos" / str(self.id) / resolution
        segment = video_path / url_segment
        return segment

    def get_thumbnail_path(self) -> Path:
        return Path(settings.MEDIA_ROOT) / "videos" / str(self.id) / "thumbnail.jpg"