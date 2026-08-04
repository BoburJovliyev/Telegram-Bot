"""
Report callbacks for /hisobot command.
"""
from datetime import datetime, timedelta, timezone
from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.repositories.unit_of_work import UnitOfWork

router = Router(name="report_callbacks_router")

@router.callback_query(F.data.startswith("report_"))
async def handle_report_callback(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Handle report period selection."""
    period = callback.data.split("_")[1]
    
    now = datetime.now(timezone.utc)
    if period == "daily":
        since = now - timedelta(days=1)
        period_name = "Kunlik (1 kun)"
    elif period == "weekly":
        since = now - timedelta(days=7)
        period_name = "Haftalik (7 kun)"
    elif period == "monthly":
        since = now - timedelta(days=30)
        period_name = "Oylik (30 kun)"
    elif period == "yearly":
        since = now - timedelta(days=365)
        period_name = "Yillik (365 kun)"
    else:
        await callback.answer("Noto'g'ri tanlov.")
        return

    chat_id = callback.message.chat.id
    
    async with session_factory() as session:
        uow = UnitOfWork(session)
        async with uow:
            total_joined, joined_via_link, top_inviters = await uow.invite_records.get_period_stats(
                group_id=chat_id,
                since=since
            )
            
    lines = [
        f"📊 <b>{period_name} hisobot:</b>\n",
        f"Jami yangi qo'shilganlar: <b>{total_joined}</b>",
        f"Shundan havola (link) orqali: <b>{joined_via_link}</b>\n"
    ]
    
    if top_inviters:
        lines.append("🏆 <b>Kim qancha odam qo'shdi:</b>")
        for i, (name, count) in enumerate(top_inviters, start=1):
            lines.append(f"{i}. {name} — {count} ta")
            
    report_text = "\n".join(lines)
    
    await callback.message.edit_text(report_text)
    await callback.answer()
