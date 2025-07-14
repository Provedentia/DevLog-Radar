from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .github import ContributionResponse


class UserBase(BaseModel):
    github_username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    github_id: Optional[int] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    github_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    contributions: List[ContributionResponse] = []
    
    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    id: int
    github_username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    total_contributions: int
    
    class Config:
        from_attributes = True