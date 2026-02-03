"""
Django management command to check mail service status
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from smart_farm.mail_service import mail_service
import asyncio


class Command(BaseCommand):
    help = 'Check the status of the asynchronous mail service'

    def handle(self, *args, **options):
        self.stdout.write('SmartFarm Mail Service Status')
        self.stdout.write('=' * 40)
        
        # Check configuration
        self.stdout.write(f'Mail Service Enabled: {getattr(settings, "MAIL_SERVICE_ENABLED", True)}')
        self.stdout.write(f'Email Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Email Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'Email Port: {settings.EMAIL_PORT}')
        self.stdout.write(f'From Email: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Site URL: {settings.SITE_URL}')
        
        # Check service status
        try:
            # Check if the service is running
            is_running = mail_service.is_running
            queue_size = mail_service.mail_queue.qsize() if hasattr(mail_service.mail_queue, 'qsize') else 'Unknown'
            
            self.stdout.write(f'\nService Status:')
            self.stdout.write(f'  Running: {is_running}')
            self.stdout.write(f'  Queue Size: {queue_size}')
            
            if is_running:
                self.stdout.write(self.style.SUCCESS('✓ Mail service is running'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Mail service is not running'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error checking service status: {e}'))
        
        # Test email configuration
        self.stdout.write(f'\nEmail Configuration Test:')
        try:
            from django.core.mail import get_connection
            connection = get_connection()
            self.stdout.write(f'  Connection: {connection.__class__.__name__}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Connection Error: {e}'))
