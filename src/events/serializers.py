from rest_framework import serializers
from .models import Event, EventRegistration
import re

class EventSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source='venue.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Event
        fields = ['id', 'name', 'event_date', 'status', 'venue', 'venue_name']


class EventRegistrSerializer(serializers.ModelSerializer):
    class Meta:
        model=EventRegistration
        fields=['id', 'event', 'full_name', 'email','confirmation_code','is_confirmed','created_at','updated_at',]
        read_only_fields=['id', 'confirmation_code', 'is_confirmed', 'created_at']

        def validate_full_name(self, value):
            if len(value)>128:
                raise serializers.ValidationError('Full name must not exceed 128 characters')
            return value
        
        def validate_email(self, value):
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, value):
                raise serializers.ValidationError('Enter a valid email address')
            return value
        
        def validate(self, data):
            event: Event=data['event']

            if event.status!="open":
                raise serializers.ValidationError('Cant register for clossed event')
            
            if EventRegistration.objects.filter(event=event, email=data['email']).exists():
                raise serializers.ValidationError('You are already registred for this event')
            
            return data
        

class EventRegistrationCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventRegistration
        fields = ("full_name", "email")
        extra_kwargs = {
            "full_name": {"max_length": 128},
        }

    def validate_full_name(self, value):
        if len(value) > 128:
            raise serializers.ValidationError("full_name must be at most 128 characters.")
        return value

    def validate_email(self, value):
        return value
