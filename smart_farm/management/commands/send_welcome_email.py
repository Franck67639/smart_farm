"""
Django management command to send welcome email to a specific user
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from smart_farm.mail_service_simple import simple_mail_service
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send welcome email to a specific user by email address'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address of the user to send welcome email to'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending the email'
        )

    def handle(self, *args, **options):
        email = options['email']
        dry_run = options['dry_run']
        
        try:
            # Find user by email
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email "{email}" does not exist')
        
        self.stdout.write(f'Found user: {user.full_name} ({user.email})')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - Would send welcome email:'))
            self.stdout.write(f'  To: {user.email}')
            self.stdout.write(f'  Subject: Welcome to SmartFarm - Your Journey Begins!')
            self.stdout.write(f'  Template: emails/welcome_email.html')
            self.stdout.write(f'  Farm: {user.farmdetails.farm_name if hasattr(user, "farmdetails") and user.farmdetails else "Not set"}')
            return
        
        try:
            # Send welcome email using simple service
            success = simple_mail_service.send_welcome_email(user)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'✓ Welcome email sent successfully to {user.email}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ Welcome email failed to send to {user.email}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send welcome email: {e}'))
            logger.error(f"Failed to send welcome email to {email}: {e}")
