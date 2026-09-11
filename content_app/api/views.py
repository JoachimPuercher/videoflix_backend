from rest_framework import generics, status
from rest_framework.response import Response
from content_app.models import Video
from .serializers import VideoSerializer
from rest_framework.permissions import IsAuthenticated
from content_app.models import Video
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404


class RetrieveVideoListView(generics.ListAPIView):

    permission_classes = [IsAuthenticated]
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class HlsMasterPlaylistView(generics.views.APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        movie_id = self.kwargs["movie_id"]

        video = get_object_or_404(Video, pk=movie_id)
        resolution = self.kwargs["resolution"]
        movie_path = video.get_path(f"{resolution}")

        if not movie_path.is_file():
            raise Http404
            
        return FileResponse(open(movie_path, "rb"), content_type="application/vnd.apple.mpegurl")