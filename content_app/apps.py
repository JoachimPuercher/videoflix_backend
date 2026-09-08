from django.apps import AppConfig


class ContentAppConfig(AppConfig):
    name = 'content_app'

    def ready(self):
        import content_app.signals