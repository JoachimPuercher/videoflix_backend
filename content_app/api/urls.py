"""Routes of the content API, mounted under /api/ in core/urls.py.

The playlist references its segments by bare file name, so the segment
route has to live directly beside the playlist route.
"""

from django.urls import path
from .views import RetrieveVideoListView, HlsMasterPlaylistView, HlsSegmentView


urlpatterns = [
    path('video/', RetrieveVideoListView.as_view(), name='video_list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', HlsMasterPlaylistView.as_view(), name='hls_manifest'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>/', HlsSegmentView.as_view(), name='hls_segment'),
]