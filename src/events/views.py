from django.shortcuts import render
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Event
from .serializers import EventSerializer

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