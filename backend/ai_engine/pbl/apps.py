from django.apps import AppConfig


class PBLConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_engine.pbl'
    label = 'pbl'
    verbose_name = 'Problem-Based Learning'

    def ready(self):
        pass  # signal registration would go here
