"""
Simplified Mail Service for SmartFarm - Production Friendly
Handles sending emails without complex asyncio that can cause worker crashes
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)


class SimpleMailService:
    """Simplified synchronous mail service for SmartFarm"""
    
    def __init__(self):
        self.enabled = getattr(settings, 'MAIL_SERVICE_ENABLED', True)
        logger.info("Simple mail service initialized")
    
    def _send_email_sync(self, mail_data: Dict[str, Any]) -> bool:
        """Send email synchronously"""
        try:
            subject = mail_data['subject']
            template_name = mail_data.get('template_name')
            context = mail_data.get('context', {})
            recipient_email = mail_data['recipient_email']
            from_email = mail_data.get('from_email', settings.DEFAULT_FROM_EMAIL)
            
            if template_name:
                # Use HTML template
                html_content = render_to_string(template_name, context)
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[recipient_email]
                )
                email.attach_alternative(html_content, "text/html")
            else:
                # Plain text email
                message = mail_data.get('message', '')
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=[recipient_email]
                )
            
            # Send email
            result = email.send()
            
            if result > 0:
                logger.info(f"Email sent successfully to {recipient_email}")
                self._log_mail_activity(mail_data, 'sent')
                return True
            else:
                logger.error(f"Email sending failed to {recipient_email}")
                self._log_mail_activity(mail_data, 'failed', 'Email send returned 0')
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            self._log_mail_activity(mail_data, 'failed', str(e))
            return False
    
    def _log_mail_activity(self, mail_data: Dict[str, Any], status: str, error: str = None):
        """Log mail activity for tracking"""
        try:
            log_entry = {
                'timestamp': timezone.now().isoformat(),
                'recipient_email': mail_data['recipient_email'],
                'subject': mail_data['subject'],
                'mail_type': mail_data.get('mail_type', 'unknown'),
                'status': status,
                'error': error
            }
            logger.info(f"Mail activity: {log_entry}")
        except Exception as e:
            logger.error(f"Failed to log mail activity: {e}")
    
    def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to new user"""
        if not self.enabled:
            logger.info("Mail service disabled, skipping welcome email")
            return False
            
        mail_data = {
            'mail_type': 'welcome',
            'subject': 'Welcome to SmartFarm - Your Journey Begins!',
            'template_name': 'emails/welcome_email.html',
            'context': {
                'user': user,
                'full_name': user.full_name,
                'email': user.email,
                'registration_date': user.date_joined.strftime('%B %d, %Y'),
                'farm_name': user.farmdetails.farm_name if hasattr(user, 'farmdetails') and user.farmdetails else 'Your Farm',
                'current_year': datetime.now().year,
                'site_url': getattr(settings, 'SITE_URL', 'https://smart-farm-yj5d.onrender.com')
            },
            'recipient_email': user.email
        }
        
        return self._send_email_sync(mail_data)
    
    def send_farm_setup_reminder(self, user: User) -> bool:
        """Send farm setup reminder email"""
        if not self.enabled:
            logger.info("Mail service disabled, skipping farm setup reminder")
            return False
            
        mail_data = {
            'mail_type': 'farm_setup_reminder',
            'subject': 'Complete Your SmartFarm Profile',
            'template_name': 'emails/farm_setup_reminder.html',
            'context': {
                'user': user,
                'full_name': user.full_name,
                'email': user.email,
                'onboarding_url': f"{getattr(settings, 'SITE_URL', 'https://smart-farm-yj5d.onrender.com')}/onboarding/",
                'current_year': datetime.now().year,
                'site_url': getattr(settings, 'SITE_URL', 'https://smart-farm-yj5d.onrender.com')
            },
            'recipient_email': user.email
        }
        
        return self._send_email_sync(mail_data)
    
    def send_weather_alert(self, user: User, alert_data: Dict[str, Any]) -> bool:
        """Send weather alert email"""
        if not self.enabled:
            logger.info("Mail service disabled, skipping weather alert")
            return False
            
        mail_data = {
            'mail_type': 'weather_alert',
            'subject': f"Weather Alert for {alert_data.get('location', 'Your Farm')}",
            'template_name': 'emails/weather_alert.html',
            'context': {
                'user': user,
                'full_name': user.full_name,
                'alert_data': alert_data,
                'current_year': datetime.now().year,
                'site_url': getattr(settings, 'SITE_URL', 'https://smart-farm-yj5d.onrender.com')
            },
            'recipient_email': user.email
        }
        
        return self._send_email_sync(mail_data)


# Global simple mail service instance
simple_mail_service = SimpleMailService()


def start_simple_mail_service():
    """Start the simple mail service (call this in Django startup)"""
    try:
        logger.info("Simple mail service started")
    except Exception as e:
        logger.error(f"Failed to start simple mail service: {e}")


# Django signal handlers
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """Handle user creation - send welcome email"""
    if created:
        # Send welcome email using simple service
        simple_mail_service.send_welcome_email(instance)
