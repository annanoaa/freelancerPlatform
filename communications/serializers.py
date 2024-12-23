from rest_framework import serializers

from users.models import User
from .models import Conversation, Message, Notification
from users.serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    read_by = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ('conversation', 'sender', 'created_at', 'read_by')

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_last_message(self, obj):
        last_message = obj.messages.first()  # Using order_by from Meta
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.exclude(read_by=user).count()

class ConversationCreateSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all()
    )
    initial_message = serializers.CharField(write_only=True)

    class Meta:
        model = Conversation
        fields = ('participants', 'project', 'initial_message')

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('recipient', 'created_at')