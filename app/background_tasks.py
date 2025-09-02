import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import crud

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def refresh_expired_invite_codes():
    """Background task to refresh invite codes every hour"""
    while True:
        try:
            db: Session = SessionLocal()
            
            # Get groups that need code refresh
            groups_to_refresh = crud.get_groups_needing_code_refresh(db)
            
            for group in groups_to_refresh:
                logger.info(f"Refreshing invite code for group: {group.name} (ID: {group.id})")
                crud.refresh_group_invite_code(db, group.id)
            
            if groups_to_refresh:
                logger.info(f"Refreshed invite codes for {len(groups_to_refresh)} groups")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error refreshing invite codes: {e}")
        
        # Wait for 1 hour
        await asyncio.sleep(3600)  # 3600 seconds = 1 hour

def start_background_tasks():
    """Start all background tasks"""
    loop = asyncio.get_event_loop()
    loop.create_task(refresh_expired_invite_codes())
    logger.info("Background tasks started")
