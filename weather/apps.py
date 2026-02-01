from django.apps import AppConfig


class WeatherConfig(AppConfig):
    name = 'weather'
    verbose_name = 'Weather Services'
    
    def ready(self):
        # Import signal handlers if needed
        pass
