from django.contrib import admin
from .models import Venue, Event

# Register your models here.

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display=["name", "id"]
    search_fields=["name"]
    list_per_page = 20

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display=["name", "event_date", "status", "venue"]
    search_fields=["name"]
    list_filter=["status", "event_date", "venue"]
    date_hierarchy="event_date"
    list_per_page = 20
    