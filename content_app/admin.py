"""Admin registration for videos; uploading here starts the ffmpeg jobs."""

from django.contrib import admin
from content_app.models import Video


class VideoAdmin(admin.ModelAdmin):
    """Show the id next to the title so API calls can be built from it."""
    list_display = ["title", "pk", "description"]

    def get_fields(self, request, obj=None):
        """Hide thumbnail_url on the add page; the worker fills it later."""
        fields = super().get_fields(request, obj)
        if obj is None:
            return [field for field in fields if field != "thumbnail_url"]
        return fields


admin.site.register(Video, VideoAdmin)
