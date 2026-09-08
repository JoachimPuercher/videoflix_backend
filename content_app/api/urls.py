from django.urls import path
from .views import RetrieveVideoListView


urlpatterns = [
    path('video/', RetrieveVideoListView.as_view(), name='video_list'),
]