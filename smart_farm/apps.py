from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class SmartFarmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smart_farm'
    verbose_name = 'SmartFarm'

    def ready(self):
        """
        Initialize ultra-lightweight mail service when app is ready
        """
        try:
            from django.conf import settings
            if getattr(settings, 'MAIL_SERVICE_ENABLED', True):
                from .mail_service_ultralight import start_ultra_light_mail_service
                start_ultra_light_mail_service()
                logger.info("SmartFarm app ready - Ultra-lightweight mail service initialized")
            else:
                logger.info("SmartFarm app ready - Mail service disabled")
        except Exception as e:
            logger.error(f"Failed to initialize ultra-lightweight mail service: {e}")
