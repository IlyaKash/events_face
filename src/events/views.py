import uuid
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Event, EventRegistration
from .serializers import EventSerializer, EventRegistrSerializer, EventRegistrationCreateSerializer
from rest_framework import status
from rest_framework.response import Response
import requests
import json

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def event_register(request, event_id):
    try:
        event=Event.objects.get(id=event_id, status='open')
    except Event.DoesNotExist:
        return Response(
            {'error' : 'Event not found or not open for registration'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer=EventRegistrationCreateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            registration=EventRegistration.objects.create(
                event=event,
                full_name=serializer.validated_data['full_name'],
                email=serializer.validated_data['email']
            )
            confirmation_code=registration.generate_confirmation_code()

            email_sent=send_confirmation_email(
                registration.email,
                registration.full_name,
                event.name,
                confirmation_code
            )

            if email_sent:
                return Response(
                    {
                        "message": "Registration successful. Confirmation code sent to your email.",
                        "registration_id": str(registration.id),
                        "confirmation_code": confirmation_code
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {
                        "message": "Registration created but failed to send confirmation email",
                        "registration_id": str(registration.id),
                        "confirmation_code": confirmation_code
                    },
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            return Response(
                {"error": f"Registration failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def send_confirmation_email(email, full_name, event_name, confirmation_code):
    notification_url="https://notifications.k3scluster.tech/api/notifications"

    headers={
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc19zdGFmZiI6ZmFsc2UsInN1YiI6IjIzIiwiZXhwIjoxNzY0MjM4NDgzLCJpYXQiOjE3NjQxNTIwODN9.NN6__xsoizzXUIIlcUlq5rxNvF62mf2XGydgqsJFiAZ8-ltNPMpgSB2-wJPXdTAFhzRwn9JrY8PcH6BXbuHjb2cQkzRUUD9p3T_A1kv7IafPuvqQCuUyyPXUpTJ6DY7bq24IHFgJu9Ib0Diz0KbFnVA_k-aj3l8atClTA2_yCvPmt7Vx5hWuW00Km-JVHptSlAvrFNv4Wvvim_4n6D1GRqjx84CVskzNnDzp5I7oaE69soe_ojIP1aKQlFcxay3b-nozR4QjWQv_NBTCC-zcZxDST4IRp4apnxBHiNJqZLmylzZswzo_O0eOyKDV5sKCZ3VlT8V5FinLsdpaymE4Bw'
    }

    payload={
        'id': str(uuid.uuid4()),
        'owner_id': '8ad9e699-dc2f-439c-a335-da9a6438ecc0',
        'email': email,
        'message' : f"""
        Здравствуйте, {full_name}!
        
        Вы успешно зарегистрировались на мероприятие: {event_name}
        
        Ваш код подтверждения: {confirmation_code}
        
        С уважением,
        Команда Events-Face
        """,
        "metadata": {
            "event_name": event_name,
            "confirmation_code": confirmation_code
        }
    }
    try:
        response = requests.post(
            notification_url,
            headers=headers,
            json=payload,
            timeout=10
        )
        print(f"Notification API response: {response.status_code} - {response.text}")
        return response.status_code == 200# сервис возвращает 201
    except requests.RequestException as e:
        print(f"Notification API error: {e}")
        return False