"""
Django management command to send farm setup reminders to users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from smart_farm.mail_service import mail_service
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send farm setup reminder emails to users who haven\'t completed their profile'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Send reminders to users registered X days ago (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show who would receive reminders without sending emails'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find users who registered X days ago but haven't completed onboarding
        users_to_remind = User.objects.filter(
            date_joined__gte=cutoff_date,
            date_joined__lt=cutoff_date + timedelta(days=1)
        ).exclude(
            farmdetails__is_completed=True
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN - Would send reminders to {users_to_remind.count()} users:')
            )
            for user in users_to_remind:
                self.stdout.write(f'  - {user.email} (registered {user.date_joined.date()})')
            return
        
        self.stdout.write(f'Found {users_to_remind.count()} users to remind...')
        
        sent_count = 0
        failed_count = 0
        
        for user in users_to_remind:
            try:
                mail_service.send_farm_setup_reminder(user)
                sent_count += 1
                self.stdout.write(f'✓ Reminder queued for {user.email}')
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to queue reminder for {user.email}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed: {sent_count} reminders queued, {failed_count} failed'
            )
        )
