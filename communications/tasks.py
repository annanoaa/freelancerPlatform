from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Message, Notification


@shared_task
def notify_new_message(message_id):
    try:
        message = Message.objects.select_related(
            'conversation',
            'sender'
        ).prefetch_related(
            'conversation__participants'
        ).get(id=message_id)

        # Create notifications for all participants except sender
        for participant in message.conversation.participants.exclude(
                id=message.sender.id
        ):
            Notification.objects.create(
                recipient=participant,
                type='MESSAGE',
                title=f'New message from {message.sender.get_full_name()}',
                message=message.content[:100] + '...' if len(message.content) > 100 else message.content,
                link=f'/conversations/{message.conversation.id}/'
            )

            # Send email notification if user has email notifications enabled
            if participant.profile.email_notifications:  # Assuming this field exists
                send_mail(
                    f'New message from {message.sender.get_full_name()}',
                    f'You have a new message in your conversation.\n\n'
                    f'Message preview: {message.content[:100]}...\n\n'
                    f'Click here to view: {settings.SITE_URL}/conversations/{message.conversation.id}/',
                    settings.DEFAULT_FROM_EMAIL,
                    [participant.email],
                    fail_silently=True
                )
    except Message.DoesNotExist:
        pass


@shared_task
def clean_old_notifications():
    """
    Delete notifications older than 30 days that have been read
    """
    from django.utils import timezone
    from datetime import timedelta

    thirty_days_ago = timezone.now() - timedelta(days=30)
    Notification.objects.filter(
        created_at__lt=thirty_days_ago,
        read=True
    ).delete()


@shared_task
def send_unread_messages_summary():
    """
    Send daily summary of unread messages to users
    """
    from django.db.models import Count
    from users.models import User

    for user in User.objects.all():
        unread_count = Message.objects.filter(
            conversation__participants=user
        ).exclude(
            read_by=user
        ).count()

        if unread_count > 0:
            send_mail(
                'Unread Messages Summary',
                f'You have {unread_count} unread messages in your conversations.\n\n'
                f'Visit {settings.SITE_URL}/conversations/ to view them.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True
            )


@shared_task
def notify_project_update(project_id, update_type, message):
    """
    Send notifications for project updates
    """
    from projects.models import Project
    try:
        project = Project.objects.select_related('client', 'freelancer').get(id=project_id)

        # Determine recipients based on project roles
        recipients = {project.client, project.freelancer} if project.freelancer else {project.client}

        for recipient in recipients:
            if recipient:  # Check if recipient exists
                Notification.objects.create(
                    recipient=recipient,
                    type='PROJECT',
                    title=f'Project Update: {project.title}',
                    message=message,
                    link=f'/projects/{project.id}/'
                )

                # Send email if notifications are enabled
                if recipient.profile.email_notifications:
                    send_mail(
                        f'Project Update: {project.title}',
                        f'{message}\n\n'
                        f'Click here to view: {settings.SITE_URL}/projects/{project.id}/',
                        settings.DEFAULT_FROM_EMAIL,
                        [recipient.email],
                        fail_silently=True
                    )
    except Project.DoesNotExist:
        pass


@shared_task
def notify_milestone_update(milestone_id, update_type):
    """
    Send notifications for milestone updates
    """
    from projects.models import Milestone
    try:
        milestone = Milestone.objects.select_related(
            'project__client',
            'project__freelancer'
        ).get(id=milestone_id)

        message = f'Milestone "{milestone.title}" has been {update_type}'

        # Notify both client and freelancer
        recipients = {milestone.project.client, milestone.project.freelancer}

        for recipient in recipients:
            if recipient:  # Check if recipient exists
                Notification.objects.create(
                    recipient=recipient,
                    type='MILESTONE',
                    title=f'Milestone Update: {milestone.title}',
                    message=message,
                    link=f'/projects/{milestone.project.id}/milestones/{milestone.id}/'
                )

                if recipient.profile.email_notifications:
                    send_mail(
                        f'Milestone Update: {milestone.title}',
                        f'{message}\n\n'
                        f'Click here to view: {settings.SITE_URL}/projects/'
                        f'{milestone.project.id}/milestones/{milestone.id}/',
                        settings.DEFAULT_FROM_EMAIL,
                        [recipient.email],
                        fail_silently=True
                    )
    except Milestone.DoesNotExist:
        pass