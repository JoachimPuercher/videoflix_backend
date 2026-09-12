"""Views of the content API: video list and HLS streaming.

All views require the JWT cookie. Files are served straight from
MEDIA_ROOT with FileResponse; unknown ids, resolutions or files are a 404.
"""

from rest_framework import generics
from content_app.models import Video
from .serializers import VideoSerializer
from .throttling import ReceiveVideoRateThrottle, VideoListThrottle
from rest_framework.permissions import IsAuthenticated
from content_app.models import Video
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404


class RetrieveVideoListView(generics.ListAPIView):
    """GET /api/video/: all videos with their thumbnail URL."""

    permission_classes = [IsAuthenticated]
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    throttle_classes = [VideoListThrottle]


class HlsMasterPlaylistView(generics.views.APIView):
    """GET /api/video/<movie_id>/<resolution>/index.m3u8: the HLS playlist."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ReceiveVideoRateThrottle]

    def get(self, request, *args, **kwargs):
        """Whitelist the resolution, then stream the playlist file."""
        movie_id = self.kwargs["movie_id"]
        video = get_object_or_404(Video, pk=movie_id)
        resolution = self.kwargs["resolution"]

        if resolution not in Video.Resolution.values:
            raise Http404

        movie_path = video.get_path(resolution)

        if not movie_path.is_file():
            raise Http404

        return FileResponse(
            open(
                movie_path,
                "rb"),
            content_type="application/vnd.apple.mpegurl")


class HlsSegmentView(generics.views.APIView):
    """GET /api/video/<movie_id>/<resolution>/<segment>/: one .ts segment.

    The URL resolver already rejects a segment name containing a slash, so
    the name can only address files inside the resolution folder.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ReceiveVideoRateThrottle]

    def get(self, request, *args, **kwargs):
        """Whitelist the resolution, then stream the segment file."""
        movie_id = self.kwargs["movie_id"]
        video = get_object_or_404(Video, pk=movie_id)
        resolution = self.kwargs["resolution"]

        if resolution not in Video.Resolution.values:
            raise Http404

        segment = self.kwargs["segment"]
        segment_path = video.get_segment(resolution, segment)

        if not segment_path.is_file():
            raise Http404

        return FileResponse(open(segment_path, "rb"),
                            content_type="video/MP2T")
