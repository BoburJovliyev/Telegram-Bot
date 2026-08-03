from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.core.enums import UserRole
from bot.filters.role_filter import RoleFilter
from bot.keyboards.inline import get_admin_dashboard_keyboard

router = Router(name="admin_cmd_router")


@router.message(Command("admin"), RoleFilter(UserRole.ADMIN))
async def cmd_admin(message: Message) -> None:
    """Handle the /admin command to show the dashboard."""
    if message.chat.type == "private":
        await message.answer("❌ This command must be used in a group.")
        return

    await message.answer(
        "🎛 <b>Admin Dashboard</b>\n\nSelect an action below:",
        reply_markup=get_admin_dashboard_keyboard()
    )
