"""Admin registration for videos; uploading here starts the ffmpeg jobs."""

from django.contrib import admin
from content_app.images import reencode_as_jpeg
from content_app.models import Video


class VideoAdmin(admin.ModelAdmin):
    """Show the id next to the title so API calls can be built from it."""
    list_display = ["title", "pk", "description"]
    # exclude = ["thumbnail_url"]

    def get_fields(self, request, obj=None):
        """Hide thumbnail_url on the add page; the worker fills it later."""
        fields = super().get_fields(request, obj)
        if obj is None:
            return [field for field in fields if field != "thumbnail_url"]
        return fields

    def save_model(self, request, obj, form, change):
        """Store a new thumbnail upload only as a freshly encoded JPEG.

        The model validator has already checked the upload at this point.
        """
        if "thumbnail_file" in form.changed_data and obj.thumbnail_file:
            obj.thumbnail_file = reencode_as_jpeg(obj.thumbnail_file)
        super().save_model(request, obj, form, change)


admin.site.register(Video, VideoAdmin)
