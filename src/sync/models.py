from django.db import models
import uuid

# Create your models here.
class SyncResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    started_at=models.DateTimeField(auto_now_add=True)
    finished_at=models.DateTimeField(null=True, blank=True)
    added_count=models.IntegerField(default=0)
    updated_count=models.IntegerField(default=0)
    is_success=models.BooleanField(default=False)
    error_message=models.TextField(blank=True, null=True)
    sync_type=models.CharField(
        max_length=11,
        choices=[('full', 'Full'), ('incremental', 'Incremental')],
        default='incremental',
    )

    class Meta:
        db_table='sync_result'
        ordering=['-started_at']
    
    def __str__(self):
        return f"Sync {self.started_at} ({self.sync_type})"

class SyncSettings(models.Model):
    key=models.CharField(max_length=100, unique=True)
    value=models.TextField(blank=True, null=True)
    description=models.TextField(blank=True, null=True)

    class Meta:
        db_table="sync_settings"

    def __str__(self):
        return self.key
