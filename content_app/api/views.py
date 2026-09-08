from rest_framework import generics
from content_app.models import Video
from .serializers import VideoSerializer


class RetrieveVideoListView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer