"""Admin registration for the built-in User model."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Django registers User itself; drop that registration to replace it below.
admin.site.unregister(User)


class VideoflixUserAdmin(UserAdmin):
    """Default UserAdmin plus the activation state as a list column."""

    list_display = UserAdmin.list_display + ("is_active",)

admin.site.register(User, VideoflixUserAdmin)