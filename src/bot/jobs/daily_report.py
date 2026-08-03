"""
Daily report scheduled job.
"""

import structlog
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.analytics.engine import AnalyticsEngine
from bot.models.admin import GroupAdmin
from bot.models.group import Group
from bot.utils.time_utils import get_current_date

logger = structlog.get_logger(__name__)

async def send_daily_reports(
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """
    Generate and send daily statistical reports to group admins.
    This job is intended to run every night (e.g., midnight).
    """
    logger.info("Starting daily report generation...")
    today = get_current_date()
    
    async with session_factory() as session:
        engine = AnalyticsEngine(session)
        
        # Get all active groups
        groups = (await session.execute(select(Group))).scalars().all()
        
        for group in groups:
            try:
                stats = await engine.calculate_daily_stats(group.id, today)
                
                # Fetch admins for this group who should receive notifications
                admins = (await session.execute(
                    select(GroupAdmin).where(GroupAdmin.group_id == group.id)
                )).scalars().all()
                
                admin_ids = [admin.user_id for admin in admins]
                # Fallback to group owner if no specific admins configured
                if not admin_ids and group.owner_id:
                    admin_ids = [group.owner_id]
                    
                if not admin_ids:
                    continue

                text = (
                    f"📊 <b>Daily Report for {group.title or 'Group'}</b>\n\n"
                    f"👥 Total Members: <b>{stats['active_members_eod']}</b>\n"
                    f"📈 Net Growth: <b>{stats['net_growth']:+}</b>\n\n"
                    f"📥 <b>New Joins:</b>\n"
                    f"• Invite Links: {stats['invite_link_joins']}\n"
                    f"• Admin Added: {stats['admin_added_joins']}\n"
                    f"• Join Requests: {stats['join_request_joins']}\n"
                    f"• Public Search: {stats['public_joins']}\n\n"
                    f"🚪 <b>Leaves:</b> {stats['leaves_count']}\n"
                    f"🎯 <b>Retention:</b> {stats['retention_rate']}%\n"
                )
                
                # Send to each admin in their private chat
                for admin_id in admin_ids:
                    try:
                        await bot.send_message(admin_id, text)
                    except Exception as e:
                        logger.warning(f"Could not send daily report to admin {admin_id}", error=str(e))
                        
            except Exception as e:
                logger.error(f"Error generating daily report for group {group.id}", error=str(e))
                
    logger.info("Daily report generation completed.")
