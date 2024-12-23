import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancerPlatform.settings')

# Create the Celery app
app = Celery('freelancerPlatform')

# Configure Celery using settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all registered Django apps
app.autodiscover_tasks()

CELERY_BEAT_SCHEDULE = {
    'clean-old-notifications': {
        'task': 'communications.tasks.clean_old_notifications',
        'schedule': timedelta(days=1),  # Run daily
    },
    'send-unread-messages-summary': {
        'task': 'communications.tasks.send_unread_messages_summary',
        'schedule': crontab(hour="9", minute="0"),  # Run daily at 9 AM
    },
}