#!/usr/bin/env python3

from app.workers.tasks import celery_app
from app.workers.scheduler import setup_periodic_tasks

if __name__ == "__main__":
    # Ensure periodic tasks are configured
    setup_periodic_tasks()
    
    # Start the Celery worker
    celery_app.start()