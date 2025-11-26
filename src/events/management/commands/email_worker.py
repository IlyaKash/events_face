import time
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from src.events.models import EmailOutbox, EmailOutboxStatus
from src.events.views import NOTIFICATIONS_URL, JWT_TOKEN

class Command(BaseCommand):
    help = "Process pending emails and send them to notifications service"

    RETRY_DELAY = 5
    def handle(self, *args, **options):
        pending_emails = EmailOutbox.objects.filter(status=EmailOutboxStatus.PENDING)
        self.stdout.write(f"Found {pending_emails.count()} emails to process.")

        headers = {"Authorization": f"Bearer {JWT_TOKEN}"}

        for outbox in pending_emails:
            sent = False
            recipient = outbox.to_email
            while not sent:
                try:
                    resp = requests.post(NOTIFICATIONS_URL, json=outbox.payload, headers=headers, timeout=5)
                    outbox.attempts += 1
                    outbox.last_attempt_at = timezone.now()

                    if resp.status_code == 200:
                        outbox.status = EmailOutboxStatus.SENT
                        sent = True
                        self.stdout.write(f"Email sent to {recipient}")
                    else:
                        outbox.status = EmailOutboxStatus.FAILED
                        self.stdout.write(
                            f"Failed to send email to {recipient}, status {resp.status_code}. Retrying in {self.RETRY_DELAY}s..."
                        )
                        time.sleep(self.RETRY_DELAY)

                    outbox.save(update_fields=["status", "attempts", "last_attempt_at"])

                except requests.RequestException as e:
                    outbox.attempts += 1
                    outbox.last_attempt_at = timezone.now()
                    outbox.status = EmailOutboxStatus.FAILED
                    outbox.save(update_fields=["status", "attempts", "last_attempt_at"])
                    self.stdout.write(
                        f"Exception for {recipient}: {e}. Retrying in {self.RETRY_DELAY}s..."
                    )
                    time.sleep(self.RETRY_DELAY)

        self.stdout.write("Processing finished.")
