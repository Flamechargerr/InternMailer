"""
Celery application configuration for the InternMailer follow-up scheduler.

This module sets up Celery with Redis as the broker and provides the main
Celery application instance for task queue processing.
"""

import os
from datetime import timedelta
from celery import Celery
from celery.schedules import crontab

# Get Redis configuration from environment
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Create Celery application
celery_app = Celery(
    'followup_scheduler',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        'scheduler.tasks',
        'scheduler.followup_tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'scheduler.tasks.process_followup_queue': {'queue': 'followups'},
        'scheduler.tasks.schedule_campaign_followups': {'queue': 'scheduling'},
        'scheduler.tasks.cleanup_completed_followups': {'queue': 'maintenance'},
        'scheduler.followup_tasks.*': {'queue': 'followups'},
    },
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Retry configuration
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Process follow-up queue every 5 minutes
        'process-followup-queue': {
            'task': 'scheduler.tasks.process_followup_queue',
            'schedule': timedelta(minutes=5),
        },
        
        # Schedule new follow-ups every hour
        'schedule-campaign-followups': {
            'task': 'scheduler.tasks.schedule_campaign_followups',
            'schedule': timedelta(hours=1),
        },
        
        # Cleanup completed follow-ups daily at 2 AM
        'cleanup-completed-followups': {
            'task': 'scheduler.tasks.cleanup_completed_followups',
            'schedule': crontab(hour=2, minute=0),
        },
        
        # Health check every 10 minutes
        'health-check': {
            'task': 'scheduler.tasks.health_check',
            'schedule': timedelta(minutes=10),
        },
    },
)

# Optional: Configure Celery monitoring
if os.getenv('CELERY_FLOWER_ENABLED', 'false').lower() == 'true':
    celery_app.conf.update(
        flower_basic_auth=[os.getenv('FLOWER_USERNAME', 'admin'), 
                          os.getenv('FLOWER_PASSWORD', 'admin')]
    )

# Task discovery
celery_app.autodiscover_tasks([
    'scheduler.tasks',
    'scheduler.followup_tasks'
])

if __name__ == '__main__':
    celery_app.start()
