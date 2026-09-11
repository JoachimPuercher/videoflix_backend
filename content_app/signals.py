from content_app.models import Video
from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import convert480p, convert720p, convert1080p
import django_rq
from pathlib import Path


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    if created:
        source_path = instance.video_file.path
        queue = django_rq.get_queue('default', autocommit=True)
        queue.enqueue(convert480p, source_path, instance.get_path("480p"))
        queue.enqueue(convert720p, source_path, instance.get_path("720p"))
        queue.enqueue(convert1080p, source_path, instance.get_path("1080p"), job_timeout=1800)



