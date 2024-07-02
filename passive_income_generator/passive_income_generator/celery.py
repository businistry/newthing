## passive_income_generator/celery.py

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'passive_income_generator.settings')

# Create a new Celery app
app = Celery('passive_income_generator')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    """
    A simple task for debugging purposes.
    Prints information about the request.
    """
    print(f'Request: {self.request!r}')

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    'update_earnings_hourly': {
        'task': 'income_streams.tasks.update_earnings',
        'schedule': 3600.0,  # Run every hour (3600 seconds)
    },
    'generate_analytics_daily': {
        'task': 'analytics.tasks.generate_daily_analytics',
        'schedule': 86400.0,  # Run daily (86400 seconds)
    },
}

# Optional: Configure Celery to use Redis as the result backend
app.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Optional: Set the maximum number of retries for failed tasks
app.conf.task_max_retries = 3

# Optional: Set the default queue for tasks
app.conf.task_default_queue = 'default'

# Optional: Configure task routing
app.conf.task_routes = {
    'income_streams.tasks.*': {'queue': 'income_streams'},
    'analytics.tasks.*': {'queue': 'analytics'},
}

# Optional: Set task serializer to JSON
app.conf.task_serializer = 'json'

# Optional: Set result serializer to JSON
app.conf.result_serializer = 'json'

# Optional: Set accepted content types
app.conf.accept_content = ['json']

if __name__ == '__main__':
    app.start()
