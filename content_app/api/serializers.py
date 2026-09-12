"""Serializers of the content API."""

from rest_framework import serializers
from content_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    """Read-only list entry; video_file stays internal on purpose."""

    class Meta:

        model = Video

        fields = [
            'id',
            'title',
            'description',
            'created_at',
            'category',
            'thumbnail_url'
        ]
        read_only_fields = [
            'id',
            'title',
            'description',
            'created_at',
            'category',
            'thumbnail_url'
        ]