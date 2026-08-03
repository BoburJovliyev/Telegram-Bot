"""
Dashboard navigation callback handlers.
"""

import structlog
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.analytics.engine import AnalyticsEngine
from bot.keyboards.factory import DashboardCallback
from bot.keyboards.inline import get_admin_dashboard_keyboard, get_export_options_keyboard
from bot.utils.time_utils import get_current_date

logger = structlog.get_logger(__name__)
router = Router(name="dashboard_cb_router")


@router.callback_query(DashboardCallback.filter(F.action == "main"))
async def back_to_main_dashboard(
    callback: CallbackQuery,
) -> None:
    """Return to the main admin dashboard."""
    await callback.message.edit_text(
        "🎛 <b>Admin Dashboard</b>\n\nSelect an action below:",
        reply_markup=get_admin_dashboard_keyboard()
    )
    await callback.answer()


@router.callback_query(DashboardCallback.filter(F.action == "stats"))
async def show_group_stats(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Show detailed group statistics."""
    group_id = callback.message.chat.id
    today = get_current_date()
    
    async with session_factory() as session:
        engine = AnalyticsEngine(session)
        stats = await engine.calculate_daily_stats(group_id, today)
        
    text = (
        f"📊 <b>Group Stats (Today)</b>\n\n"
        f"👥 Active Members: <b>{stats['active_members_eod']}</b>\n"
        f"📈 Net Growth: <b>{stats['net_growth']:+}</b>\n\n"
        f"<b>Joins Breakdown:</b>\n"
        f"• Invite Links: {stats['invite_link_joins']}\n"
        f"• Admin Added: {stats['admin_added_joins']}\n"
        f"• Join Requests: {stats['join_request_joins']}\n"
        f"• Public Search: {stats['public_joins']}\n"
        f"• Rejoins: {stats['rejoin_count']}\n\n"
        f"🚪 Left/Kicked: {stats['leaves_count']}\n"
        f"🎯 Retention Rate: {stats['retention_rate']}%\n"
    )
    
    # We could add a "Back" button here, but for simplicity we edit and provide a back button
    from bot.keyboards.inline import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Back", callback_data=DashboardCallback(action="main"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(DashboardCallback.filter(F.action == "export"))
async def show_export_options(callback: CallbackQuery) -> None:
    """Show export format selection."""
    await callback.message.edit_text(
        "📥 <b>Export Data</b>\n\nSelect the format for the group leaderboard:",
        reply_markup=get_export_options_keyboard()
    )
    await callback.answer()


@router.callback_query(DashboardCallback.filter(F.action == "settings"))
async def show_settings(callback: CallbackQuery) -> None:
    """Show group settings (placeholder)."""
    # Settings implementation will come in a later phase
    from bot.keyboards.inline import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Back", callback_data=DashboardCallback(action="main"))
    
    await callback.message.edit_text(
        "⚙️ <b>Settings</b>\n\nSettings management is under construction.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()
