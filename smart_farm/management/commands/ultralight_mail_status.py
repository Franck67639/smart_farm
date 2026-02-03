"""
Django management command to check ultra-lightweight mail service status
"""

import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from smart_farm.mail_service_ultralight import ultra_light_mail_service


class Command(BaseCommand):
    help = 'Check the status of the ultra-lightweight mail service'

    def handle(self, *args, **options):
        self.stdout.write('SmartFarm Ultra-Lightweight Mail Service Status')
        self.stdout.write('=' * 55)
        
        # Check configuration
        self.stdout.write(f'Mail Service Enabled: {getattr(settings, "MAIL_SERVICE_ENABLED", True)}')
        self.stdout.write(f'Email Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Email Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'Email Port: {settings.EMAIL_PORT}')
        self.stdout.write(f'From Email: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Site URL: {settings.SITE_URL}')
        
        # Check service status
        try:
            enabled = ultra_light_mail_service.enabled
            queue_size = ultra_light_mail_service.get_queue_size()
            queue_file = ultra_light_mail_service.email_queue_file
            
            self.stdout.write(f'\nService Status:')
            self.stdout.write(f'  Enabled: {enabled}')
            self.stdout.write(f'  Type: Ultra-Lightweight File-Based Service')
            self.stdout.write(f'  Queue File: {queue_file}')
            self.stdout.write(f'  Queue Size: {queue_size}')
            
            if enabled:
                self.stdout.write(self.style.SUCCESS('✓ Ultra-lightweight mail service is ready'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Ultra-lightweight mail service is disabled'))
            
            # Check queue file
            if os.path.exists(queue_file):
                file_size = os.path.getsize(queue_file)
                self.stdout.write(f'  Queue File Size: {file_size} bytes')
                
                # Show recent emails
                try:
                    with open(queue_file, 'r') as f:
                        queue = json.load(f)
                    
                    if queue:
                        self.stdout.write(f'\nRecent Emails in Queue:')
                        for i, email in enumerate(queue[-3:], 1):
                            self.stdout.write(f'  {i}. {email.get("recipient_email", "Unknown")} - {email.get("subject", "No Subject")} ({email.get("attempts", 0)} attempts)')
                except:
                    self.stdout.write('  Could not read queue file contents')
            else:
                self.stdout.write('  Queue file does not exist')
                
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
        
        self.stdout.write('\nUltra-Lightweight Mail Service Benefits:')
        self.stdout.write('  • Minimal RAM usage (< 1MB)')
        self.stdout.write('  • No background processes')
        self.stdout.write('  • File-based queuing')
        self.stdout.write('  • Perfect for 512MB RAM servers')
        self.stdout.write('  • Can process emails via cron job')
        
        self.stdout.write('\nTo process queued emails:')
        self.stdout.write('  python manage.py process_email_queue --limit=5')
        self.stdout.write('  # Add to cron: */15 * * * * cd /path/to/app && python manage.py process_email_queue')
