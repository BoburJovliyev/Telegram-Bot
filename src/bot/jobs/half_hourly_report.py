"""
Half-hourly daily report job.
"""
import structlog
from datetime import datetime, timezone
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.repositories.unit_of_work import UnitOfWork

logger = structlog.get_logger(__name__)

async def send_half_hourly_reports(bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Sends a report every half hour to group/channel owners about who added how many members today.
    """
    logger.info("Starting half-hourly daily report job")
    
    # Start of the current day (UTC)
    now = datetime.now(timezone.utc)
    since = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    async with session_factory() as session:
        uow = UnitOfWork(session)
        async with uow:
            groups = await uow.groups.get_active_groups()
            
            for group in groups:
                if not group.owner_id:
                    continue
                    
                total_joined, joined_via_link, top_inviters = await uow.invite_records.get_period_stats(
                    group_id=group.id,
                    since=since
                )
                
                if total_joined == 0:
                    continue
                    
                # Format the report
                lines = [
                    f"📊 <b>{group.title}</b> guruhi/kanali uchun BUGUNGI hisobot (shu vaqtgacha):\n",
                    f"Jami yangi qo'shilganlar: <b>{total_joined}</b>",
                    f"Shundan havola (link) orqali: <b>{joined_via_link}</b>\n"
                ]
                
                if top_inviters:
                    lines.append("🏆 <b>Kim qancha odam qo'shdi:</b>")
                    for i, (name, count) in enumerate(top_inviters, start=1):
                        lines.append(f"{i}. {name} — {count} ta")
                
                report_text = "\n".join(lines)
                
                try:
                    await bot.send_message(group.owner_id, report_text)
                    logger.info("Sent half-hourly daily report", group_id=group.id, owner_id=group.owner_id)
                except Exception as e:
                    logger.error("Failed to send half-hourly report", group_id=group.id, owner_id=group.owner_id, error=str(e))
