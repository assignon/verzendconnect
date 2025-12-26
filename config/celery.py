"""
Celery configuration for VerzendConnect project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('verzendconnect')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Check for overdue rentals every day at 9:00 AM
    'check-overdue-rentals-daily': {
        'task': 'apps.notifications.tasks.check_overdue_rentals',
        'schedule': crontab(hour=9, minute=0),
    },
    # Process rental returns every day at midnight
    'process-returned-rentals-daily': {
        'task': 'apps.notifications.tasks.process_returned_rentals',
        'schedule': crontab(hour=0, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

