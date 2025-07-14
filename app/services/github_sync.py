import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..core.config import settings
from ..models import User, Contribution
from ..schemas import ContributionCreate

logger = logging.getLogger(__name__)


class GitHubSyncService:
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def get_authenticated_user(self) -> Optional[Dict[str, Any]]:
        """Get the authenticated GitHub user information."""
        if not self.token:
            logger.error("GitHub token not configured")
            return None
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/user", 
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to get authenticated user: {e}")
                return None
    
    async def get_user_repos(self, username: str) -> List[Dict[str, Any]]:
        """Get all repositories for a user."""
        repos = []
        page = 1
        per_page = 100
        
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"{self.base_url}/users/{username}/repos",
                        headers=self.headers,
                        params={"page": page, "per_page": per_page, "sort": "updated"}
                    )
                    response.raise_for_status()
                    page_repos = response.json()
                    
                    if not page_repos:
                        break
                        
                    repos.extend(page_repos)
                    page += 1
                    
                except httpx.HTTPError as e:
                    logger.error(f"Failed to get repos for {username}: {e}")
                    break
                    
        return repos
    
    async def get_commits_for_repo(
        self, 
        owner: str, 
        repo: str, 
        author: str, 
        since: datetime
    ) -> List[Dict[str, Any]]:
        """Get commits for a specific repository."""
        commits = []
        page = 1
        per_page = 100
        
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"{self.base_url}/repos/{owner}/{repo}/commits",
                        headers=self.headers,
                        params={
                            "author": author,
                            "since": since.isoformat(),
                            "page": page,
                            "per_page": per_page
                        }
                    )
                    response.raise_for_status()
                    page_commits = response.json()
                    
                    if not page_commits:
                        break
                        
                    commits.extend(page_commits)
                    page += 1
                    
                except httpx.HTTPError as e:
                    logger.error(f"Failed to get commits for {owner}/{repo}: {e}")
                    break
                    
        return commits
    
    async def get_commit_details(
        self, 
        owner: str, 
        repo: str, 
        sha: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific commit."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/commits/{sha}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to get commit details for {sha}: {e}")
                return None
    
    async def sync_user_contributions(
        self, 
        db: Session, 
        username: str, 
        days_back: int = 30
    ) -> int:
        """Sync contributions for a specific user."""
        logger.info(f"Starting GitHub sync for user: {username}")
        
        # Get or create user
        user = db.query(User).filter(User.github_username == username).first()
        if not user:
            # Get user info from GitHub
            user_info = await self.get_authenticated_user()
            if not user_info and username:
                # Fallback: create user with minimal info
                user = User(github_username=username)
                db.add(user)
                db.commit()
                db.refresh(user)
            elif user_info:
                user = User(
                    github_username=user_info["login"],
                    email=user_info.get("email"),
                    full_name=user_info.get("name"),
                    avatar_url=user_info.get("avatar_url"),
                    github_id=user_info["id"]
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        
        if not user:
            logger.error(f"Could not create or find user: {username}")
            return 0
        
        # Calculate date range
        since = datetime.utcnow() - timedelta(days=days_back)
        
        # Get user repositories
        repos = await self.get_user_repos(username)
        contributions_count = 0
        
        for repo_data in repos:
            repo_name = repo_data["full_name"]
            repo_url = repo_data["html_url"]
            owner = repo_data["owner"]["login"]
            repo = repo_data["name"]
            
            # Get commits for this repo
            commits = await self.get_commits_for_repo(owner, repo, username, since)
            
            for commit_data in commits:
                commit_sha = commit_data["sha"]
                
                # Check if we already have this contribution
                existing = db.query(Contribution).filter(
                    Contribution.commit_sha == commit_sha
                ).first()
                
                if existing:
                    continue
                
                # Get detailed commit information
                commit_details = await self.get_commit_details(owner, repo, commit_sha)
                
                if not commit_details:
                    continue
                
                # Parse commit data
                commit_date = datetime.fromisoformat(
                    commit_data["commit"]["author"]["date"].replace("Z", "+00:00")
                )
                
                stats = commit_details.get("stats", {})
                
                contribution = Contribution(
                    user_id=user.id,
                    repo_name=repo_name,
                    repo_url=repo_url,
                    commit_sha=commit_sha,
                    commit_message=commit_data["commit"]["message"],
                    commit_url=commit_data["html_url"],
                    commit_date=commit_date,
                    additions=stats.get("additions", 0),
                    deletions=stats.get("deletions", 0),
                    files_changed=len(commit_details.get("files", []))
                )
                
                db.add(contribution)
                contributions_count += 1
        
        db.commit()
        logger.info(f"Synced {contributions_count} contributions for {username}")
        return contributions_count


github_sync_service = GitHubSyncService()