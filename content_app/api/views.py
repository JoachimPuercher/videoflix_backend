"""Views of the content API: video list and HLS streaming.

All views require the JWT cookie. Files are served straight from
MEDIA_ROOT with FileResponse; unknown ids, resolutions or files are a 404.
"""

from pathlib import Path

from rest_framework import generics
from content_app.models import Video
from .serializers import VideoSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from content_app.models import Video
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404


class RetrieveVideoListView(generics.ListAPIView):
    """GET /api/video/: all videos with their thumbnail URL."""

    permission_classes = [IsAuthenticated]
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class HlsMasterPlaylistView(generics.views.APIView):
    """GET /api/video/<movie_id>/<resolution>/index.m3u8: the HLS playlist."""

    permission_classes = [IsAuthenticated]

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


class VideoThumbnailView(generics.views.APIView):
    """GET /api/video/<movie_id>/thumbnail.jpg: the preview image.

    An uploaded thumbnail wins over the frame grabbed by the worker; both
    are JPEGs, because uploads are re-encoded on save. Public on purpose: the frontend loads it with a plain <img> tag, which
    sends no cookie when frontend and API run on different sites. Served
    by Django so it also works with DEBUG=False, where the development
    media route in core/urls.py no longer exists.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Stream the thumbnail; 404 if there is none (yet)."""
        video = get_object_or_404(Video, pk=self.kwargs["movie_id"])
        if video.thumbnail_file:
            thumbnail_path = Path(video.thumbnail_file.path)
        else:
            thumbnail_path = video.get_thumbnail_path()

        if not thumbnail_path.is_file():
            raise Http404

        response = FileResponse(open(thumbnail_path, "rb"),
                                content_type="image/jpeg")
        # Let browsers and proxies keep it for a day.
        # response["Cache-Control"] = "public, max-age=86400"
        return response
