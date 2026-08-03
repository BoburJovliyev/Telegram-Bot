"""
Database cleanup scheduled job.
"""

import structlog
from datetime import timedelta
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.models.invite_record import InviteRecord
from bot.utils.time_utils import get_current_datetime

logger = structlog.get_logger(__name__)

async def cleanup_old_records(
    session_factory: async_sessionmaker[AsyncSession],
    days_to_keep: int = 90
) -> None:
    """
    Remove old, inactive invite records (e.g. leaves) to maintain performance.
    Only removes records where the user has left the group.
    """
    logger.info(f"Starting database cleanup (keeping last {days_to_keep} days)...")
    
    cutoff_date = get_current_datetime() - timedelta(days=days_to_keep)
    
    async with session_factory() as session:
        try:
            # Delete invite records where the user has left AND the leave date is older than cutoff
            stmt = delete(InviteRecord).where(
                InviteRecord.left_at != None,
                InviteRecord.left_at < cutoff_date
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            logger.info(f"Cleanup completed. Removed {result.rowcount} old records.")
            
        except Exception as e:
            await session.rollback()
            logger.error("Error during database cleanup", error=str(e))
