from django.db import models
from pathlib import Path
from typing import Literal
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

    Quality = Literal["_480p", "_720p", "_1080p"]

    def get_path(self, quality_string:Quality) -> str:
        path = Path(self.video_file.path)
        name = path.with_suffix("")
        new_file_name = f"{name}{quality_string}.mp4"
        return new_file_name