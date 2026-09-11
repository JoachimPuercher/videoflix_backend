from django.contrib import admin
from content_app.models import Video

# Register your models here.

class VideoAdmin(admin.ModelAdmin):
    list_display = ["title", "pk", "description"]
    pass

admin.site.register(Video, VideoAdmin)