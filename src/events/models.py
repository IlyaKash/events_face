from django.db import models
import uuid

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