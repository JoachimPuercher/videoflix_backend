from rest_framework import serializers
from content_app.models import Video

class VideoSerializer(serializers.ModelSerializer):

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