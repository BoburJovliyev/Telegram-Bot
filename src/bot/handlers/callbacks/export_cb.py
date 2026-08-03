"""
Export callback handlers.
"""

import structlog
from aiogram import Router
from aiogram.types import BufferedInputFile, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.keyboards.factory import ExportCallback
from bot.models.member import Member
from bot.reports.exporter import Exporter

logger = structlog.get_logger(__name__)
router = Router(name="export_cb_router")


@router.callback_query(ExportCallback.filter())
async def handle_export(
    callback: CallbackQuery,
    callback_data: ExportCallback,
    session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Handle export requests for the group leaderboard."""
    group_id = callback.message.chat.id
    fmt = callback_data.format
    
    await callback.message.edit_text("⏳ Generating report, please wait...")
    
    try:
        async with session_factory() as session:
            # Fetch all members with their users for this group, sorted by total_invited
            stmt = (
                select(Member)
                .where(Member.group_id == group_id)
                .order_by(Member.total_invited.desc())
            )
            result = await session.execute(stmt)
            members = result.scalars().all()
            
        if not members:
            await callback.message.edit_text("❌ No members found to export.")
            return

        if fmt == "csv":
            file_data = Exporter.generate_leaderboard_csv(members)
            file_name = f"leaderboard_{group_id}.csv"
        elif fmt == "excel":
            file_data = Exporter.generate_leaderboard_excel(members)
            file_name = f"leaderboard_{group_id}.xlsx"
        else:
            await callback.message.edit_text("❌ Unsupported format.")
            return

        input_file = BufferedInputFile(file_data, filename=file_name)
        
        await callback.message.answer_document(
            document=input_file,
            caption=f"📊 Here is the exported leaderboard for the group."
        )
        
        # Restore the main dashboard view
        from bot.keyboards.inline import get_admin_dashboard_keyboard
        await callback.message.edit_text(
            "🎛 <b>Admin Dashboard</b>\n\nSelect an action below:",
            reply_markup=get_admin_dashboard_keyboard()
        )

    except Exception as e:
        logger.exception("Failed to generate export", error=str(e))
        await callback.message.edit_text("❌ An error occurred while generating the report.")
        
    finally:
        await callback.answer()
