from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class SmartFarmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smart_farm'
    verbose_name = 'SmartFarm'

    def ready(self):
        """
        Initialize mail service when app is ready
        """
        try:
            from django.conf import settings
            if getattr(settings, 'MAIL_SERVICE_ENABLED', True):
                from .mail_service import start_mail_service
                start_mail_service()
                logger.info("SmartFarm app ready - Mail service initialized")
            else:
                logger.info("SmartFarm app ready - Mail service disabled")
        except Exception as e:
            logger.error(f"Failed to initialize mail service: {e}")
