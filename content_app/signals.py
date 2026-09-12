"""Start the background jobs for a newly uploaded video.

Registered in ContentAppConfig.ready(). Only the first save triggers the
jobs; later edits (title, description) do not re-encode anything.
"""

from content_app.models import Video
from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import create_thumbnail, convert480p, convert720p, convert1080p
import django_rq
from pathlib import Path


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """Enqueue thumbnail and the three HLS renditions for a new video."""
    if created:
        source_path = instance.video_file.path
        queue = django_rq.get_queue('default', autocommit=True)
        queue.enqueue(create_thumbnail, instance.id)
        queue.enqueue(
            convert480p,
            source_path,
            instance.get_path(
                Video.Resolution.P480))
        queue.enqueue(
            convert720p,
            source_path,
            instance.get_path(
                Video.Resolution.P720))
        queue.enqueue(
            convert1080p,
            source_path,
            instance.get_path(
                Video.Resolution.P1080),
            job_timeout=1800)
