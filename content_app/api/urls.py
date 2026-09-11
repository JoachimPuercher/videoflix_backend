from django.urls import path
from .views import RetrieveVideoListView, HlsMasterPlaylistView


urlpatterns = [
    path('video/', RetrieveVideoListView.as_view(), name='video_list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', HlsMasterPlaylistView.as_view(), name='hls_manifest'),
]