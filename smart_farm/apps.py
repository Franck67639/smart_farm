from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class SmartFarmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smart_farm'
    verbose_name = 'SmartFarm'

    def ready(self):
        """
        Initialize simple mail service when app is ready
        """
        try:
            from django.conf import settings
            if getattr(settings, 'MAIL_SERVICE_ENABLED', True):
                from .mail_service_simple import start_simple_mail_service
                start_simple_mail_service()
                logger.info("SmartFarm app ready - Simple mail service initialized")
            else:
                logger.info("SmartFarm app ready - Mail service disabled")
        except Exception as e:
            logger.error(f"Failed to initialize simple mail service: {e}")
