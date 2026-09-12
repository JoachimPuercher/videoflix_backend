"""Admin registration for videos; uploading here starts the ffmpeg jobs."""

from django.contrib import admin
from content_app.models import Video


class VideoAdmin(admin.ModelAdmin):
    """Show the id next to the title so API calls can be built from it."""
    list_display = ["title", "pk", "description"]


admin.site.register(Video, VideoAdmin)
