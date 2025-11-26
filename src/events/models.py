from django.db import models
import uuid
import random

# Create your models here.
class Venue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name=models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table="venues"
    
    def __str__(self):
        return self.name

class EventStatus(models.TextChoices):
    OPEN= "open", "Open"
    CLOSED="closed", "Closed"

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name=models.CharField(max_length=255)
    event_date=models.DateTimeField()
    status=models.CharField(
        max_length=10, choices=EventStatus.choices, default=EventStatus.OPEN
    )
    venue=models.ForeignKey(
        Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name="events"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table="events"
        ordering=["-event_date"]
    
    def __str__(self):
        return self.name

class EventRegistration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event=models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registration')
    full_name=models.CharField(max_length=128)
    email=models.EmailField()
    confirmation_code=models.CharField(max_length=6, blank=True)
    is_confirmed=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        db_table="event_registration"
        unique_together=['event', 'email'] #один имеил один ивент
    
    def __str__(self):
        return f"{self.full_name} - {self.event.name}"
    
    def generate_confirmation_code(self):
        self.confirmation_code=str(random.randint(100000, 999999))
        self.save()
        return self.confirmation_code


class EmailOutboxStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"

class EmailOutbox(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    payload = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=16, choices=EmailOutboxStatus.choices, default=EmailOutboxStatus.PENDING)
    attempts = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "email_outbox"