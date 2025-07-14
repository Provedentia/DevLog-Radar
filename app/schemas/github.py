from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class GitHubSyncRequest(BaseModel):
    username: Optional[str] = None
    days_back: int = 30


class GitHubSyncResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None
    contributions_synced: Optional[int] = None


class ContributionBase(BaseModel):
    repo_name: str
    repo_url: Optional[str] = None
    commit_sha: str
    commit_message: Optional[str] = None
    commit_url: Optional[str] = None
    commit_date: datetime
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0


class ContributionCreate(ContributionBase):
    user_id: int


class ContributionResponse(ContributionBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActivitySummary(BaseModel):
    date: str
    commit_count: int
    total_additions: int
    total_deletions: int
    repos_touched: int


class ActivitySummaryResponse(BaseModel):
    username: str
    period_start: datetime
    period_end: datetime
    total_commits: int
    daily_activity: List[ActivitySummary]
    
    class Config:
        from_attributes = True