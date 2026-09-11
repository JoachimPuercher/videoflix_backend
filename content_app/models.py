from django.db import models
from pathlib import Path
from typing import Literal
from django.conf import settings
from pathlib import Path

# Create your models here.

class Video(models.Model):

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail_url = models.URLField(max_length=200)
    category = models.CharField(max_length=40)
    video_file = models.FileField()

    def __str__(self):
        return self.title

    Quality = Literal["480p", "720p", "1080p"]

    def get_path(self, resolution:Quality) -> Path:
        video_path = Path(settings.MEDIA_ROOT) / "videos" / str(self.id) / resolution 
        video_path.mkdir(parents=True, exist_ok=True)
        playlist = video_path / "index.m3u8"
        return playlist