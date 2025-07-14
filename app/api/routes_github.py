from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Optional

from ..core.database import get_db
from ..models import User, Contribution
from ..schemas import GitHubSyncRequest, GitHubSyncResponse, ActivitySummaryResponse, ActivitySummary
from ..workers.tasks import sync_github_data

router = APIRouter(prefix="/sync", tags=["GitHub Sync"])


@router.post("/github", response_model=GitHubSyncResponse)
async def sync_github_contributions(
    request: GitHubSyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Queue a GitHub sync job for a user.
    
    - **username**: GitHub username to sync (optional, defaults to authenticated user)
    - **days_back**: Number of days to look back for contributions (default: 30)
    """
    username = request.username
    
    if not username:
        raise HTTPException(
            status_code=400, 
            detail="Username is required for GitHub sync"
        )
    
    try:
        # Queue the sync task
        task = sync_github_data.delay(username, request.days_back)
        
        return GitHubSyncResponse(
            success=True,
            message=f"GitHub sync queued for user: {username}",
            task_id=task.id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue GitHub sync: {str(e)}"
        )


@router.get("/github/status/{task_id}")
async def get_sync_status(task_id: str):
    """Get the status of a GitHub sync task."""
    from ..workers.tasks import celery_app
    
    task = celery_app.AsyncResult(task_id)
    
    if task.state == "PENDING":
        return {"status": "pending", "message": "Task is waiting to be processed"}
    elif task.state == "PROGRESS":
        return {"status": "in_progress", "message": "Task is being processed"}
    elif task.state == "SUCCESS":
        return {
            "status": "completed",
            "message": "Task completed successfully",
            "result": task.result
        }
    elif task.state == "FAILURE":
        return {
            "status": "failed",
            "message": "Task failed",
            "error": str(task.info)
        }
    else:
        return {"status": task.state, "message": f"Task state: {task.state}"}


@router.get("/activity/summary/{username}", response_model=ActivitySummaryResponse)
async def get_activity_summary(
    username: str,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get a summary of user activity over the specified time period.
    
    - **username**: GitHub username
    - **days_back**: Number of days to include in summary (default: 30)
    """
    # Find user
    user = db.query(User).filter(User.github_username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Get contributions in the date range
    contributions = db.query(Contribution).filter(
        Contribution.user_id == user.id,
        Contribution.commit_date >= start_date,
        Contribution.commit_date <= end_date
    ).all()
    
    # Group by date
    daily_activity = {}
    total_commits = 0
    
    for contrib in contributions:
        date_str = contrib.commit_date.strftime("%Y-%m-%d")
        
        if date_str not in daily_activity:
            daily_activity[date_str] = {
                "date": date_str,
                "commit_count": 0,
                "total_additions": 0,
                "total_deletions": 0,
                "repos_touched": set()
            }
        
        daily_activity[date_str]["commit_count"] += 1
        daily_activity[date_str]["total_additions"] += contrib.additions
        daily_activity[date_str]["total_deletions"] += contrib.deletions
        daily_activity[date_str]["repos_touched"].add(contrib.repo_name)
        total_commits += 1
    
    # Convert to response format
    daily_summary = []
    for date_str in sorted(daily_activity.keys()):
        activity = daily_activity[date_str]
        daily_summary.append(ActivitySummary(
            date=activity["date"],
            commit_count=activity["commit_count"],
            total_additions=activity["total_additions"],
            total_deletions=activity["total_deletions"],
            repos_touched=len(activity["repos_touched"])
        ))
    
    return ActivitySummaryResponse(
        username=username,
        period_start=start_date,
        period_end=end_date,
        total_commits=total_commits,
        daily_activity=daily_summary
    )