"""Rate limits for the video endpoints.

The views require a logged in user, so the limits count per user
(UserRateThrottle). The rates live in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].
"""

from rest_framework.throttling import UserRateThrottle


class VideoListThrottle(UserRateThrottle):
    """One call per page load; a human never needs many."""
    scope = 'video_list'


class ReceiveVideoRateThrottle(UserRateThrottle):
    """Playlists and segments: a film is hundreds of requests, keep it high."""
    scope = 'receive_video'
