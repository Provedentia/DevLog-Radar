from celery.schedules import crontab
from .tasks import celery_app


def setup_periodic_tasks():
    """Configure periodic tasks for the Celery app."""
    
    celery_app.conf.beat_schedule = {
        # Sync GitHub data every day at 2 AM UTC
        'sync-github-daily': {
            'task': 'app.workers.tasks.sync_all_users_github',
            'schedule': crontab(hour=2, minute=0),
        },
        
        # Sync LeetCode data every day at 3 AM UTC
        'sync-leetcode-daily': {
            'task': 'app.workers.tasks.sync_all_users_leetcode',
            'schedule': crontab(hour=3, minute=0),
        },
        
        # Optional: More frequent sync during business hours
        # 'sync-github-frequent': {
        #     'task': 'app.workers.tasks.sync_all_users_github',
        #     'schedule': crontab(minute=0, hour='9-17'),  # Every hour from 9 AM to 5 PM
        # },
    }
    
    celery_app.conf.timezone = 'UTC'


# Initialize periodic tasks
setup_periodic_tasks()