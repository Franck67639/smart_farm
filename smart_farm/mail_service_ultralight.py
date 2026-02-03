"""
Ultra-Lightweight Mail Service for SmartFarm - Designed for 512MB RAM servers
Minimal resource usage with deferred email processing
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)


class UltraLightMailService:
    """Ultra-lightweight mail service for minimal resource servers"""
    
    def __init__(self):
        self.enabled = getattr(settings, 'MAIL_SERVICE_ENABLED', True)
        self.email_queue_file = getattr(settings, 'BASE_DIR') / 'email_queue.json'
        logger.info("Ultra-lightweight mail service initialized")
    
    def _queue_email(self, mail_data: Dict[str, Any]) -> bool:
        """Queue email to file for later processing"""
        try:
            # Create queue file if it doesn't exist
            if not os.path.exists(self.email_queue_file):
                with open(self.email_queue_file, 'w') as f:
                    json.dump([], f)
            
            # Read existing queue
            try:
                with open(self.email_queue_file, 'r') as f:
                    queue = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                queue = []
            
            # Add email to queue
            mail_entry = {
                'timestamp': timezone.now().isoformat(),
                'subject': mail_data['subject'],
                'template_name': mail_data.get('template_name'),
                'context': mail_data.get('context', {}),
                'recipient_email': mail_data['recipient_email'],
                'from_email': mail_data.get('from_email', settings.DEFAULT_FROM_EMAIL),
                'mail_type': mail_data.get('mail_type', 'unknown'),
                'attempts': 0
            }
            
            queue.append(mail_entry)
            
            # Write back to file
            with open(self.email_queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
            
            logger.info(f"Email queued for {mail_data['recipient_email']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue email: {e}")
            return False
    
    def send_welcome_email(self, user: User) -> bool:
        """Queue welcome email for new user"""
        if not self.enabled:
            logger.info("Mail service disabled, skipping welcome email")
            return False
            
        mail_data = {
            'mail_type': 'welcome',
            'subject': 'Welcome to SmartFarm - Your Journey Begins!',
            'template_name': 'emails/welcome_email.html',
            'context': {
                'user': {
                    'full_name': user.full_name,
                    'email': user.email
                },
                'full_name': user.full_name,
                'email': user.email,
                'registration_date': user.date_joined.strftime('%B %d, %Y'),
                'farm_name': user.farmdetails.farm_name if hasattr(user, 'farmdetails') and user.farmdetails else 'Your Farm',
                'current_year': datetime.now().year,
                'site_url': getattr(settings, 'SITE_URL', 'https://smart-farm-yj5d.onrender.com')
            },
            'recipient_email': user.email
        }
        
        return self._queue_email(mail_data)
    
    def send_farm_setup_reminder(self, user: User) -> bool:
        """Queue farm setup reminder email"""
        if not self.enabled:
            logger.info("Mail service disabled, skipping farm setup reminder")
            return False
            
        mail_data = {
            'mail_type': 'farm_setup_reminder',
            'subject': 'Complete Your SmartFarm Profile',
            'template_name': 'emails/farm_setup_reminder.html',
            'context': {
                'user': {
                    'full_name': user.full_name,
                    'email': user.email
                },
                'full_name': user.full_name,
                'email': user.email,
                'onboarding_url': f"{getattr(settings, 'SITE_URL', 'https://smart-farm-yj5d.onrender.com')}/onboarding/",
                'current_year': datetime.now().year,
                'site_url': getattr(settings, 'SITE_URL', 'https://smart-farm-yj5d.onrender.com')
            },
            'recipient_email': user.email
        }
        
        return self._queue_email(mail_data)
    
    def send_weather_alert(self, user: User, alert_data: Dict[str, Any]) -> bool:
        """Queue weather alert email"""
        if not self.enabled:
            logger.info("Mail service disabled, skipping weather alert")
            return False
            
        mail_data = {
            'mail_type': 'weather_alert',
            'subject': f"Weather Alert for {alert_data.get('location', 'Your Farm')}",
            'template_name': 'emails/weather_alert.html',
            'context': {
                'user': {
                    'full_name': user.full_name,
                    'email': user.email
                },
                'full_name': user.full_name,
                'alert_data': alert_data,
                'current_year': datetime.now().year,
                'site_url': getattr(settings, 'SITE_URL', 'https://smart-farm-yj5d.onrender.com')
            },
            'recipient_email': user.email
        }
        
        return self._queue_email(mail_data)
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        try:
            if not os.path.exists(self.email_queue_file):
                return 0
            
            with open(self.email_queue_file, 'r') as f:
                queue = json.load(f)
            return len(queue)
        except:
            return 0
    
    def clear_queue(self) -> bool:
        """Clear the email queue"""
        try:
            with open(self.email_queue_file, 'w') as f:
                json.dump([], f)
            logger.info("Email queue cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear email queue: {e}")
            return False


# Global ultra-lightweight mail service instance
ultra_light_mail_service = UltraLightMailService()


def start_ultra_light_mail_service():
    """Start the ultra-lightweight mail service"""
    try:
        logger.info("Ultra-lightweight mail service started - File-based queuing")
    except Exception as e:
        logger.error(f"Failed to start ultra-lightweight mail service: {e}")
