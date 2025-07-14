from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..core.database import get_db
from ..models import User, Contribution
from ..schemas import UserCreate, UserUpdate, UserResponse, UserSummary

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(
        User.github_username == user.github_username
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="User with this GitHub username already exists"
        )
    
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/", response_model=List[UserSummary])
async def list_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """List all users with contribution counts."""
    users = db.query(
        User.id,
        User.github_username,
        User.full_name,
        User.avatar_url,
        func.count(Contribution.id).label("total_contributions")
    ).outerjoin(Contribution).group_by(User.id).offset(skip).limit(limit).all()
    
    return [
        UserSummary(
            id=user.id,
            github_username=user.github_username,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            total_contributions=user.total_contributions or 0
        )
        for user in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/username/{username}", response_model=UserResponse)
async def get_user_by_username(username: str, db: Session = Depends(get_db)):
    """Get a specific user by GitHub username."""
    user = db.query(User).filter(User.github_username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db)
):
    """Update a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user and all their contributions."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete associated contributions first
    db.query(Contribution).filter(Contribution.user_id == user_id).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}