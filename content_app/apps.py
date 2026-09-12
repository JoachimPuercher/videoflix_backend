"""App config for videos, HLS transcoding and streaming."""

from django.apps import AppConfig


class ContentAppConfig(AppConfig):
    """Referenced by its full path in INSTALLED_APPS so ready() is used."""
    name = 'content_app'

    def ready(self):
        """Import the signal receivers once all models are loaded."""
        import content_app.signals
