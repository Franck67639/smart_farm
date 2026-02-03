"""
Django management command to manually process the mail queue
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from smart_farm.mail_service import mail_service
import asyncio
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manually process the mail queue (useful for debugging)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Timeout in seconds for processing (default: 30)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Maximum number of emails to process (default: 10)'
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        max_count = options['count']
        
        self.stdout.write('Processing Mail Queue')
        self.stdout.write('=' * 30)
        
        try:
            # Check queue size
            if hasattr(mail_service.mail_queue, 'qsize'):
                queue_size = mail_service.mail_queue.qsize()
                self.stdout.write(f'Queue size: {queue_size}')
            else:
                self.stdout.write('Queue size: Unknown')
            
            # Process queue synchronously
            async def process_queue():
                processed = 0
                while processed < max_count:
                    try:
                        # Get mail from queue with timeout
                        mail_task = await asyncio.wait_for(
                            mail_service.mail_queue.get(), 
                            timeout=1.0
                        )
                        
                        self.stdout.write(f'Processing email {processed + 1}: {mail_task.get("recipient_email", "Unknown")}')
                        
                        # Send the email
                        await mail_service._send_mail_async(mail_task)
                        mail_service.mail_queue.task_done()
                        
                        processed += 1
                        self.stdout.write(self.style.SUCCESS(f'✓ Email {processed} sent'))
                        
                    except asyncio.TimeoutError:
                        if processed == 0:
                            self.stdout.write('No emails in queue')
                        break
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'✗ Error processing email: {e}'))
                        logger.error(f"Error processing mail: {e}")
                        break
                
                return processed
            
            # Run the async processing
            processed_count = asyncio.run(process_queue())
            
            self.stdout.write(self.style.SUCCESS(f'Processed {processed_count} emails'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to process mail queue: {e}'))
            logger.error(f"Failed to process mail queue: {e}")
