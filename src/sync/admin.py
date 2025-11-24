from django.contrib import admin
from .models import SyncResult, SyncSettings


@admin.register(SyncResult)
class SyncResultAdmin(admin.ModelAdmin):
    list_display = ["started_at", "finished_at", "sync_type", "added_count", "updated_count", "is_success"]
    list_filter = ["sync_type", "is_success", "started_at"]
    readonly_fields = ["started_at", "finished_at"]
    ordering = ["-started_at"]


@admin.register(SyncSettings)
class SyncSettingsAdmin(admin.ModelAdmin):
    list_display = ["key", "value", "description"]
    readonly_fields = ["key"]