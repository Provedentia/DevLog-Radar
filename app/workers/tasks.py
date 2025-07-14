from celery import Celery
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.database import SessionLocal
from ..services.github_sync import github_sync_service
from ..services.leetcode_sync import leetcode_sync_service
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    "devlog_radar",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
)


@celery_app.task(bind=True)
def sync_github_data(self, username: str, days_back: int = 30):
    """Celery task to sync GitHub data for a user."""
    try:
        logger.info(f"Starting GitHub sync task for user: {username}")
        
        db: Session = SessionLocal()
        try:
            contributions_count = github_sync_service.sync_user_contributions(
                db, username, days_back
            )
            
            logger.info(f"GitHub sync completed for {username}: {contributions_count} contributions")
            return {
                "success": True,
                "username": username,
                "contributions_synced": contributions_count,
                "message": f"Successfully synced {contributions_count} contributions"
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"GitHub sync failed for {username}: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)


@celery_app.task(bind=True)
def sync_leetcode_data(self, username: str, days_back: int = 30):
    """Celery task to sync LeetCode data for a user."""
    try:
        logger.info(f"Starting LeetCode sync task for user: {username}")
        
        db: Session = SessionLocal()
        try:
            submissions_count = leetcode_sync_service.sync_user_leetcode_data(
                db, username, days_back
            )
            
            logger.info(f"LeetCode sync completed for {username}: {submissions_count} submissions")
            return {
                "success": True,
                "username": username,
                "submissions_synced": submissions_count,
                "message": f"Successfully synced {submissions_count} submissions"
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"LeetCode sync failed for {username}: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)


@celery_app.task
def sync_all_users_github():
    """Periodic task to sync GitHub data for all active users."""
    try:
        logger.info("Starting periodic GitHub sync for all users")
        
        db: Session = SessionLocal()
        try:
            from ..models import User
            
            users = db.query(User).filter(User.is_active == True).all()
            
            for user in users:
                # Queue individual sync tasks
                sync_github_data.delay(user.github_username)
                
            logger.info(f"Queued GitHub sync for {len(users)} users")
            return {
                "success": True,
                "users_queued": len(users),
                "message": f"Queued sync for {len(users)} users"
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Periodic GitHub sync failed: {exc}")
        raise


@celery_app.task
def sync_all_users_leetcode():
    """Periodic task to sync LeetCode data for all active users."""
    try:
        logger.info("Starting periodic LeetCode sync for all users")
        
        db: Session = SessionLocal()
        try:
            from ..models import User
            
            users = db.query(User).filter(User.is_active == True).all()
            
            for user in users:
                # Queue individual sync tasks
                sync_leetcode_data.delay(user.github_username)
                
            logger.info(f"Queued LeetCode sync for {len(users)} users")
            return {
                "success": True,
                "users_queued": len(users),
                "message": f"Queued LeetCode sync for {len(users)} users"
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Periodic LeetCode sync failed: {exc}")
        raise