from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Max
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Conversation, Message, Notification
from .serializers import (
    ConversationSerializer, ConversationCreateSerializer,
    MessageSerializer, NotificationSerializer
)

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Conversation.objects.none()

        queryset = Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            'participants',
            'messages'
        ).annotate(
            last_message_time=Max('messages__created_at'),
            unread_count=Count(
                'messages',
                filter=~Q(messages__read_by=self.request.user)
            )
        ).order_by('-last_message_time')

        cache_key = f'conversations_{self.request.user.id}'
        cached_queryset = cache.get(cache_key)
        if cached_queryset is not None:
            return cached_queryset

        cache.set(cache_key, queryset, timeout=300)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer

    def perform_create(self, serializer):
        conversation = serializer.save()
        initial_message = serializer.validated_data.get('initial_message')
        if initial_message:
            Message.objects.create(
                conversation=conversation,
                sender=self.request.user,
                content=initial_message
            )

    @swagger_auto_schema(
        operation_summary="Mark all messages as read",
        responses={200: "Messages marked as read"}
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        conversation = self.get_object()
        unread_messages = conversation.messages.exclude(read_by=request.user)
        for message in unread_messages:
            message.read_by.add(request.user)
        return Response({'status': 'messages marked as read'})

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages within conversations.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()

        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related(
            'sender'
        ).prefetch_related(
            'read_by'
        )

    def perform_create(self, serializer):
        conversation = Conversation.objects.get(
            pk=self.kwargs['conversation_pk']
        )
        serializer.save(
            conversation=conversation,
            sender=self.request.user
        )
        # Update conversation timestamp
        conversation.save()  # This updates the updated_at field

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing user notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'read']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()

        return Notification.objects.filter(
            recipient=self.request.user
        )

    @swagger_auto_schema(
        operation_summary="Mark notification as read",
        responses={200: NotificationSerializer}
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response(self.get_serializer(notification).data)

    @swagger_auto_schema(
        operation_summary="Mark all notifications as read",
        responses={200: "All notifications marked as read"}
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(read=True)
        return Response({'status': 'all notifications marked as read'})