"""
Django management command to test email sending directly
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test email sending directly (bypassing mail queue)'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address to send test email to'
        )
        parser.add_argument(
            '--template',
            action='store_true',
            help='Send HTML template email instead of plain text'
        )

    def handle(self, *args, **options):
        email = options['email']
        use_template = options['template']
        
        self.stdout.write(f'Testing email to: {email}')
        self.stdout.write('=' * 40)
        
        try:
            if use_template:
                # Send HTML template email
                user = User.objects.get(email=email)
                
                # Render template
                context = {
                    'user': user,
                    'full_name': user.full_name,
                    'email': user.email,
                    'registration_date': user.date_joined.strftime('%B %d, %Y'),
                    'farm_name': user.farmdetails.farm_name if hasattr(user, 'farmdetails') and user.farmdetails else 'Your Farm',
                    'current_year': 2024,
                    'site_url': 'http://127.0.0.1:8000'
                }
                
                html_content = render_to_string('emails/welcome_email.html', context)
                text_content = strip_tags(html_content)
                
                email_msg = EmailMultiAlternatives(
                    subject='Test: Welcome to SmartFarm - Your Journey Begins!',
                    body=text_content,
                    from_email='SmartFarm Cameroon <noreply@smartfarm.cm>',
                    to=[email]
                )
                email_msg.attach_alternative(html_content, "text/html")
                
                result = email_msg.send()
                self.stdout.write(self.style.SUCCESS(f'✓ HTML template email sent (return code: {result})'))
                
            else:
                # Send plain text email
                result = send_mail(
                    subject='Test Email from SmartFarm',
                    message='This is a test email from SmartFarm Cameroon.\n\nIf you receive this, email configuration is working correctly!',
                    from_email='SmartFarm Cameroon <noreply@smartfarm.cm>',
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                self.stdout.write(self.style.SUCCESS(f'✓ Plain text email sent (return code: {result})'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Email test failed: {e}'))
            logger.error(f"Email test failed: {e}")
            
            # Show configuration for debugging
            self.stdout.write('\nEmail Configuration:')
            from django.conf import settings
            self.stdout.write(f'  EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
            self.stdout.write(f'  EMAIL_HOST: {settings.EMAIL_HOST}')
            self.stdout.write(f'  EMAIL_PORT: {settings.EMAIL_PORT}')
            self.stdout.write(f'  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
            self.stdout.write(f'  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
            self.stdout.write(f'  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
