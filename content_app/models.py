from django.db import models

# Create your models here.

class Video(models.Model):

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail_url = models.URLField(max_length=200)
    category = models.CharField(max_length=40)