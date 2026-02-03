"""
Asynchronous Mail Service for SmartFarm
Handles sending welcome emails and other notifications asynchronously
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)


class AsyncMailService:
    """Asynchronous mail service for SmartFarm"""
    
    def __init__(self):
        self.mail_queue = asyncio.Queue()
        self.is_running = False
        self.background_task = None
    
    async def start_background_processor(self):
        """Start the background mail processor"""
        if not self.is_running:
            self.is_running = True
            self.background_task = asyncio.create_task(self._process_mail_queue())
            logger.info("Async mail service started")
    
    async def stop_background_processor(self):
        """Stop the background mail processor"""
        self.is_running = False
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
        logger.info("Async mail service stopped")
    
    async def _process_mail_queue(self):
        """Background task to process mail queue"""
        while self.is_running:
            try:
                # Wait for mail task with timeout
                mail_task = await asyncio.wait_for(self.mail_queue.get(), timeout=1.0)
                await self._send_mail_async(mail_task)
                self.mail_queue.task_done()
            except asyncio.TimeoutError:
                # No mail in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing mail queue: {e}")
                continue
    
    async def _send_mail_async(self, mail_data: Dict[str, Any]):
        """Send mail asynchronously"""
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
            
            # Send email (this is synchronous but runs in async context)
            await asyncio.get_event_loop().run_in_executor(
                None, email.send
            )
            
            logger.info(f"Email sent successfully to {recipient_email}")
            
            # Log mail activity
            await self._log_mail_activity(mail_data, 'sent')
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            await self._log_mail_activity(mail_data, 'failed', str(e))
    
    async def _log_mail_activity(self, mail_data: Dict[str, Any], status: str, error: str = None):
        """Log mail activity for tracking"""
        try:
            # This could be enhanced to save to database
            log_entry = {
                'timestamp': timezone.now().isoformat(),
                'recipient_email': mail_data['recipient_email'],
                'subject': mail_data['subject'],
                'mail_type': mail_data.get('mail_type', 'unknown'),
                'status': status,
                'error': error
            }
            logger.info(f"Mail activity logged: {log_entry}")
        except Exception as e:
            logger.error(f"Failed to log mail activity: {e}")
    
    def send_welcome_email(self, user: User):
        """Queue welcome email for new user"""
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
                'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
            },
            'recipient_email': user.email
        }
        
        # Try to send email with proper fallback logic
        try:
            # First try: Use queue if service is running
            if self.is_running:
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.run_coroutine_threadsafe(
                        self.mail_queue.put(mail_data), 
                        loop
                    )
                    logger.info(f"Welcome email queued for {user.email}")
                    return  # Success, exit early
                except (RuntimeError, Exception) as e:
                    logger.warning(f"Queue failed, trying immediate send: {e}")
            
            # Second try: Send immediately if queue failed or service not running
            asyncio.run(self._send_mail_async(mail_data))
            logger.info(f"Welcome email sent immediately to {user.email}")
                    
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            # Final fallback: try one more time with direct Django email
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.template.loader import render_to_string
                from django.utils.html import strip_tags
                
                html_content = render_to_string(mail_data['template_name'], mail_data['context'])
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject=mail_data['subject'],
                    body=text_content,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartfarm.cm'),
                    to=[mail_data['recipient_email']]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                
                logger.info(f"Welcome email sent via Django fallback to {user.email}")
            except Exception as fallback_error:
                logger.error(f"Failed to send welcome email via Django fallback: {fallback_error}")
    
    def send_farm_setup_reminder(self, user: User):
        """Queue farm setup reminder email"""
        mail_data = {
            'mail_type': 'farm_setup_reminder',
            'subject': 'Complete Your SmartFarm Profile',
            'template_name': 'emails/farm_setup_reminder.html',
            'context': {
                'user': user,
                'full_name': user.full_name,
                'email': user.email,
                'onboarding_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/onboarding/",
                'current_year': datetime.now().year,
                'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
            },
            'recipient_email': user.email
        }
        
        # Try to send email with proper fallback logic
        try:
            # First try: Use queue if service is running
            if self.is_running:
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.run_coroutine_threadsafe(
                        self.mail_queue.put(mail_data), 
                        loop
                    )
                    logger.info(f"Farm setup reminder queued for {user.email}")
                    return  # Success, exit early
                except (RuntimeError, Exception) as e:
                    logger.warning(f"Queue failed, trying immediate send: {e}")
            
            # Second try: Send immediately if queue failed or service not running
            asyncio.run(self._send_mail_async(mail_data))
            logger.info(f"Farm setup reminder sent immediately to {user.email}")
                    
        except Exception as e:
            logger.error(f"Failed to send farm setup reminder: {e}")
            # Final fallback: try one more time with direct Django email
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.template.loader import render_to_string
                from django.utils.html import strip_tags
                
                html_content = render_to_string(mail_data['template_name'], mail_data['context'])
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject=mail_data['subject'],
                    body=text_content,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartfarm.cm'),
                    to=[mail_data['recipient_email']]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                
                logger.info(f"Farm setup reminder sent via Django fallback to {user.email}")
            except Exception as fallback_error:
                logger.error(f"Failed to send farm setup reminder via Django fallback: {fallback_error}")
    
    def send_weather_alert(self, user: User, alert_data: Dict[str, Any]):
        """Queue weather alert email"""
        mail_data = {
            'mail_type': 'weather_alert',
            'subject': f"Weather Alert for {alert_data.get('location', 'Your Farm')}",
            'template_name': 'emails/weather_alert.html',
            'context': {
                'user': user,
                'full_name': user.full_name,
                'alert_data': alert_data,
                'current_year': datetime.now().year,
                'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
            },
            'recipient_email': user.email
        }
        
        # Try to send email with proper fallback logic
        try:
            # First try: Use queue if service is running
            if self.is_running:
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.run_coroutine_threadsafe(
                        self.mail_queue.put(mail_data), 
                        loop
                    )
                    logger.info(f"Weather alert queued for {user.email}")
                    return  # Success, exit early
                except (RuntimeError, Exception) as e:
                    logger.warning(f"Queue failed, trying immediate send: {e}")
            
            # Second try: Send immediately if queue failed or service not running
            asyncio.run(self._send_mail_async(mail_data))
            logger.info(f"Weather alert sent immediately to {user.email}")
                    
        except Exception as e:
            logger.error(f"Failed to send weather alert: {e}")
            # Final fallback: try one more time with direct Django email
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.template.loader import render_to_string
                from django.utils.html import strip_tags
                
                html_content = render_to_string(mail_data['template_name'], mail_data['context'])
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject=mail_data['subject'],
                    body=text_content,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartfarm.cm'),
                    to=[mail_data['recipient_email']]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                
                logger.info(f"Weather alert sent via Django fallback to {user.email}")
            except Exception as fallback_error:
                logger.error(f"Failed to send weather alert via Django fallback: {fallback_error}")


# Global mail service instance
mail_service = AsyncMailService()


def start_mail_service():
    """Start the mail service (call this in Django startup)"""
    try:
        # Create event loop if not exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Start the background processor in a thread-safe way
        if loop.is_running():
            # If loop is already running, schedule the task
            asyncio.create_task(mail_service.start_background_processor())
        else:
            # If loop is not running, run it in background
            import threading
            def run_mail_service():
                asyncio.run(mail_service.start_background_processor())
            
            thread = threading.Thread(target=run_mail_service, daemon=True)
            thread.start()
        
        logger.info("Mail service initialized")
    except Exception as e:
        logger.error(f"Failed to start mail service: {e}")


def stop_mail_service():
    """Stop the mail service (call this in Django shutdown)"""
    try:
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(
            mail_service.stop_background_processor(), 
            loop
        )
        logger.info("Mail service shutdown")
    except Exception as e:
        logger.error(f"Failed to stop mail service: {e}")


# Django signal handlers
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """Handle user creation - send welcome email"""
    if created:
        # Send welcome email asynchronously
        mail_service.send_welcome_email(instance)
