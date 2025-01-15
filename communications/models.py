from django.db import models
from django.conf import settings
from users.models import User
from projects.models import Project

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='conversations',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(
        User,
        related_name='read_messages',
        blank=True
    )
    attachment = models.FileField(
        upload_to='message_attachments/%Y/%m/%d/',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['sender']),
        ]

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('MESSAGE', 'New Message'),
        ('BID', 'New Bid'),
        ('PROJECT', 'Project Update'),
        ('MILESTONE', 'Milestone Update'),
        ('RATING', 'New Rating'),
        ('SYSTEM', 'System Notification')
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True)  # Optional link to related content
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient']),
            models.Index(fields=['type']),
            models.Index(fields=['read']),
            models.Index(fields=['created_at']),
        ]