#!/usr/bin/env python3

import sys
import asyncio
import argparse
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.services.github_sync import github_sync_service
from app.services.leetcode_sync import leetcode_sync_service
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def sync_github(username: str, days_back: int = 30):
    """Manually sync GitHub data for a user."""
    logger.info(f"Starting manual GitHub sync for {username}")
    
    db = SessionLocal()
    try:
        contributions_count = await github_sync_service.sync_user_contributions(
            db, username, days_back
        )
        logger.info(f"Successfully synced {contributions_count} contributions for {username}")
        return contributions_count
    except Exception as e:
        logger.error(f"GitHub sync failed for {username}: {e}")
        raise
    finally:
        db.close()


async def sync_leetcode(username: str, days_back: int = 30):
    """Manually sync LeetCode data for a user."""
    logger.info(f"Starting manual LeetCode sync for {username}")
    
    db = SessionLocal()
    try:
        submissions_count = await leetcode_sync_service.sync_user_leetcode_data(
            db, username, days_back
        )
        logger.info(f"Successfully synced {submissions_count} submissions for {username}")
        return submissions_count
    except Exception as e:
        logger.error(f"LeetCode sync failed for {username}: {e}")
        raise
    finally:
        db.close()


async def sync_all_platforms(username: str, days_back: int = 30):
    """Sync data from all platforms for a user."""
    logger.info(f"Starting full sync for {username}")
    
    github_count = await sync_github(username, days_back)
    leetcode_count = await sync_leetcode(username, days_back)
    
    logger.info(
        f"Full sync completed for {username}: "
        f"{github_count} GitHub contributions, {leetcode_count} LeetCode submissions"
    )
    
    return {
        "github_contributions": github_count,
        "leetcode_submissions": leetcode_count
    }


def main():
    parser = argparse.ArgumentParser(description="Manual sync script for Devlog Radar")
    parser.add_argument("username", help="GitHub username to sync")
    parser.add_argument(
        "--platform", 
        choices=["github", "leetcode", "all"],
        default="all",
        help="Platform to sync (default: all)"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=30,
        help="Number of days to look back (default: 30)"
    )
    
    args = parser.parse_args()
    
    print(f"=€ Starting manual sync for {args.username}")
    print(f"=Å Looking back {args.days} days")
    print(f"=' Platform: {args.platform}")
    print("-" * 50)
    
    try:
        if args.platform == "github":
            result = asyncio.run(sync_github(args.username, args.days))
            print(f" GitHub sync completed: {result} contributions")
            
        elif args.platform == "leetcode":
            result = asyncio.run(sync_leetcode(args.username, args.days))
            print(f" LeetCode sync completed: {result} submissions")
            
        elif args.platform == "all":
            result = asyncio.run(sync_all_platforms(args.username, args.days))
            print(f" Full sync completed:")
            print(f"   =Ê GitHub: {result['github_contributions']} contributions")
            print(f"   >à LeetCode: {result['leetcode_submissions']} submissions")
        
        print("-" * 50)
        print("<‰ Sync completed successfully!")
        
    except Exception as e:
        print(f"L Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()