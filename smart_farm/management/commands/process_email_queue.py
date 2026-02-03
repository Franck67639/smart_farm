"""
Django management command to process the ultra-lightweight email queue
Designed for minimal resource usage - can be run via cron job
"""

import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from smart_farm.mail_service_ultralight import ultra_light_mail_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process the ultra-lightweight email queue (file-based)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Maximum number of emails to process (default: 5)'
        )
        parser.add_argument(
            '--clear-failed',
            action='store_true',
            help='Clear emails that have failed 3+ times'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        clear_failed = options['clear_failed']
        
        self.stdout.write('Processing Ultra-Lightweight Email Queue')
        self.stdout.write('=' * 50)
        
        queue_file = ultra_light_mail_service.email_queue_file
        
        try:
            # Read queue
            if not os.path.exists(queue_file):
                self.stdout.write('No email queue file found')
                return
            
            with open(queue_file, 'r') as f:
                queue = json.load(f)
            
            if not queue:
                self.stdout.write('Email queue is empty')
                return
            
            self.stdout.write(f'Found {len(queue)} emails in queue')
            
            # Filter out failed emails if requested
            if clear_failed:
                original_count = len(queue)
                queue = [email for email in queue if email.get('attempts', 0) < 3]
                removed = original_count - len(queue)
                if removed > 0:
                    self.stdout.write(f'Removed {removed} emails with 3+ failed attempts')
            
            # Process emails
            processed = 0
            failed = 0
            remaining_queue = []
            
            for email_data in queue[:limit]:
                try:
                    self.stdout.write(f'Processing email {processed + 1}: {email_data.get("recipient_email", "Unknown")}')
                    
                    # Send email
                    success = self._send_email(email_data)
                    
                    if success:
                        processed += 1
                        self.stdout.write(self.style.SUCCESS(f'✓ Email sent to {email_data["recipient_email"]}'))
                    else:
                        failed += 1
                        # Increment attempts and keep in queue
                        email_data['attempts'] = email_data.get('attempts', 0) + 1
                        remaining_queue.append(email_data)
                        self.stdout.write(self.style.WARNING(f'✗ Email failed for {email_data["recipient_email"]} (attempt {email_data["attempts"]})'))
                        
                except Exception as e:
                    failed += 1
                    email_data['attempts'] = email_data.get('attempts', 0) + 1
                    remaining_queue.append(email_data)
                    self.stdout.write(self.style.ERROR(f'✗ Error processing email: {e}'))
            
            # Keep unprocessed emails in queue
            remaining_queue.extend(queue[limit:])
            
            # Write back remaining emails
            with open(queue_file, 'w') as f:
                json.dump(remaining_queue, f, indent=2)
            
            self.stdout.write(self.style.SUCCESS(f'Processed {processed} emails, {failed} failed'))
            if remaining_queue:
                self.stdout.write(f'{len(remaining_queue)} emails remain in queue')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to process email queue: {e}'))
            logger.error(f"Failed to process email queue: {e}")
    
    def _send_email(self, email_data):
        """Send individual email"""
        try:
            subject = email_data['subject']
            template_name = email_data.get('template_name')
            context = email_data.get('context', {})
            recipient_email = email_data['recipient_email']
            from_email = email_data.get('from_email', settings.DEFAULT_FROM_EMAIL)
            
            if template_name:
                # Use HTML template
                html_content = render_to_string(template_name, context)
                text_content = strip_tags(html_content)
                
                email_msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[recipient_email]
                )
                email_msg.attach_alternative(html_content, "text/html")
            else:
                # Plain text email
                message = email_data.get('message', '')
                email_msg = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=[recipient_email]
                )
            
            # Send email
            result = email_msg.send()
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            return False
