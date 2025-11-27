from django.utils import timezone
import uuid
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from src.authentication import serializers
from .models import EmailOutbox, EmailOutboxStatus, Event, EventRegistration, EventStatus
from .serializers import EventSerializer, EventRegistrSerializer, EventRegistrationCreateSerializer
from rest_framework import status
from rest_framework.response import Response
import requests
import json
from django.db import IntegrityError, transaction

class EventPagination(PageNumberPagination):
    page_size=10
    page_size_query_param='page_size'
    max_page_size=100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def events_view(request):
    queryset=Event.objects.filter(status='open').select_related('venue')

    name_filter=request.GET.get('name')
    if name_filter:
        #по частичному совпадению (подойдут Рок-концерт, концерт васи пупкина.)
        queryset=queryset.filter(name__icontains=name_filter)

    ordering = request.GET.get('ordering', 'event_date')
    if ordering in ['event_date', '-event_date']:
        queryset=queryset.order_by(ordering)
    
    paginator=EventPagination()
    paginated_queryset=paginator.paginate_queryset(queryset, request)

    serializer=EventSerializer(paginated_queryset, many=True)

    return paginator.get_paginated_response(serializer.data)


NOTIFICATIONS_URL = "https://notifications.k3scluster.tech/api/notifications"
OWNER_ID = "8ad9e699-dc2f-439c-a335-da9a6438ecc0"
JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc19zdGFmZiI6ZmFsc2UsInN1YiI6IjIzIiwiZXhwIjoxNzY0MjU1ODMwLCJpYXQiOjE3NjQxNjk0MzB9.led4PTKxs-MEykb0H4qpLPSzAKw1Z4yvJRDwBaKRPzRBQ7QAvVqju7BYOz8ZZmsBQKq07Kk1Fg97NQibD9BP0PMyXqPE_wZR-nHB1Q3UHob4MInmn-GetVu1x8i_qGCbEuMcly6rSAc6WCzH4RroiRwSxS8oiD1Z12vvWAveiP705U8PuUlEGfDai8rM7_og8KXq6YEaw-Ch9TaLgC4SpcJQAUHJAfZ_ix1Cuxm-XbUgNwBqyAoiU6fczqe3W8tNUOP1aUD6xw-8f0oGWERa0ZQU-YSqkiCEcHmvvSzK-SchrmZtRTxArlPdDVqX3G6XEl-AtSPSUWYzkrz7yRO97w"

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def event_register(request, event_id):

    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({"detail": "event not found"}, status=status.HTTP_404_NOT_FOUND)

    if event.status != EventStatus.OPEN:
        return Response({"detail": "event is not open"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = EventRegistrationCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    full_name = serializer.validated_data['full_name']
    email = serializer.validated_data['email']

    try:
        with transaction.atomic():
            event = Event.objects.select_for_update().get(id=event_id)
            if EventRegistration.objects.filter(event=event, email__iexact=email).exists():
                return Response({"detail": "this email already registered"}, status=status.HTTP_400_BAD_REQUEST)

            registration = EventRegistration.objects.create(
                event=event,
                full_name=full_name,
                email=email
            )
            code = registration.generate_confirmation_code()

            payload = {
                "id": str(uuid.uuid4()),
                "owner_id": OWNER_ID,
                "email": email,
                "message": f"Здравствуйте {full_name}, ваш код подтверждения: {code}"
            }

            outbox = EmailOutbox.objects.create(
                to_email=email,
                subject=f"Подтверждение регистрации: {event.name}",
                body=payload["message"],
                payload=payload,
                status="pending"
            )
    except Exception as e:
        return Response({"detail": str(e)}, status=500)

    

    return Response({
        "registration_id": str(registration.id),
        "email_status": "queued"
    }, status=201)
