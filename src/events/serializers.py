from rest_framework import serializers
from .models import Event, Venue

class EventSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source='venue.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Event
        fields = ['id', 'name', 'event_date', 'status', 'venue', 'venue_name']