"""
Django management command to check simple mail service status
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from smart_farm.mail_service_simple import simple_mail_service


class Command(BaseCommand):
    help = 'Check the status of the simple mail service'

    def handle(self, *args, **options):
        self.stdout.write('SmartFarm Simple Mail Service Status')
        self.stdout.write('=' * 45)
        
        # Check configuration
        self.stdout.write(f'Mail Service Enabled: {getattr(settings, "MAIL_SERVICE_ENABLED", True)}')
        self.stdout.write(f'Email Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Email Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'Email Port: {settings.EMAIL_PORT}')
        self.stdout.write(f'From Email: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Site URL: {settings.SITE_URL}')
        
        # Check service status
        try:
            enabled = simple_mail_service.enabled
            self.stdout.write(f'\nService Status:')
            self.stdout.write(f'  Enabled: {enabled}')
            self.stdout.write(f'  Type: Simple Synchronous Service')
            
            if enabled:
                self.stdout.write(self.style.SUCCESS('✓ Simple mail service is ready'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Simple mail service is disabled'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error checking service status: {e}'))
        
        # Test email configuration
        self.stdout.write(f'\nEmail Configuration Test:')
        try:
            from django.core.mail import get_connection
            connection = get_connection()
            self.stdout.write(f'  Connection: {connection.__class__.__name__}')
            self.stdout.write(self.style.SUCCESS('✓ Email configuration appears valid'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Connection Error: {e}'))
        
        self.stdout.write('\nSimple Mail Service Benefits:')
        self.stdout.write('  • No asyncio - prevents worker crashes')
        self.stdout.write('  • Synchronous sending - immediate delivery')
        self.stdout.write('  • Production friendly - works on all platforms')
        self.stdout.write('  • Memory efficient - no background processes')
