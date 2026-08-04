"""
Centralized APScheduler setup.
"""

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from aiogram import Bot

from bot.jobs.stats_aggregator import aggregate_daily_stats
from bot.jobs.daily_report import send_daily_reports
from bot.jobs.cleanup import cleanup_old_records

logger = structlog.get_logger(__name__)

def setup_scheduler(
    scheduler: AsyncIOScheduler,
    session_factory: async_sessionmaker[AsyncSession],
    bot: Bot
) -> None:
    """
    Register all recurring background jobs.
    """
    logger.info("Registering background jobs...")
    
    from bot.jobs.hourly_report import send_hourly_reports
    
    # 0. Hourly Summary Report (runs at the top of every hour)
    scheduler.add_job(
        send_hourly_reports,
        trigger="cron",
        minute=0,
        kwargs={"bot": bot, "session_factory": session_factory},
        id="hourly_reports",
        replace_existing=True,
    )
    
    # 1. Raw stat aggregation (runs every 30 mins)
    scheduler.add_job(
        aggregate_daily_stats,
        trigger="interval",
        minutes=30,
        kwargs={"session_factory": session_factory},
        id="aggregate_daily_stats",
        replace_existing=True,
    )
    
    # 2. Daily Summary Report (runs at midnight UTC)
    scheduler.add_job(
        send_daily_reports,
        trigger="cron",
        hour=0,
        minute=0,
        kwargs={"bot": bot, "session_factory": session_factory},
        id="daily_reports",
        replace_existing=True,
    )
    
    # 3. Database Cleanup (runs every Sunday at 02:00 AM)
    scheduler.add_job(
        cleanup_old_records,
        trigger="cron",
        day_of_week="sun",
        hour=2,
        minute=0,
        kwargs={"session_factory": session_factory, "days_to_keep": 90},
        id="db_cleanup",
        replace_existing=True,
    )
