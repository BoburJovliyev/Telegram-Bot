"""
Background Jobs.

Contains scheduled tasks that run via APScheduler.
"""

from datetime import datetime, timezone
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.analytics.engine import AnalyticsEngine
from bot.repositories.unit_of_work import UnitOfWork

logger = structlog.get_logger(__name__)


async def aggregate_daily_stats(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Scheduled job that calculates and upserts daily statistics
    for all active groups in the database.
    """
    logger.info("Starting daily stats aggregation job")
    
    # We use UTC for all database dates
    today = datetime.now(timezone.utc).date()
    
    async with session_factory() as session:
        uow = UnitOfWork(session)
        analytics = AnalyticsEngine(session)
        
        try:
            # Get all active groups
            active_groups = await uow.groups.get_active_groups()
            
            for group in active_groups:
                try:
                    # 1. Calculate statistics
                    stats_data = await analytics.calculate_daily_stats(group.id, today)
                    
                    # 2. Upsert into DailyStats table
                    await uow.daily_stats.upsert_stats(
                        group_id=group.id,
                        stats_date=today,
                        **stats_data
                    )
                    
                    # Commit per group so one failure doesn't fail all groups
                    await uow.commit()
                    
                    logger.debug(
                        "Aggregated stats for group", 
                        group_id=group.id, 
                        joins=stats_data["joins_count"]
                    )
                    
                except Exception as e:
                    await uow.rollback()
                    logger.error(
                        "Failed to aggregate stats for group", 
                        group_id=group.id, 
                        error=str(e)
                    )
            
            logger.info("Daily stats aggregation job completed", processed=len(active_groups))
            
        except Exception as e:
            logger.exception("Fatal error in stats aggregation job", error=str(e))
