"""
Basic command handlers.
"""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.services.group_service import GroupService

router = Router(name="commands_router")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle the /start command."""
    if message.chat.type == "private":
        await message.answer(
            "👋 Welcome to the Enterprise Invite Tracker Bot!\n\n"
            "Add me to your group, grant me administrator permissions "
            "(specifically 'Invite Users'), and I will automatically "
            "start tracking who invites whom."
        )
    else:
        await message.answer(
            "👋 I am awake and monitoring this group."
        )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle the /help command."""
    await message.answer(
        "📚 <b>Bot Help</b>\n\n"
        "<b>Available Commands:</b>\n"
        "/start - Start the bot\n"
        "/help - Show this message\n"
        "/stats - Show your invite statistics\n"
        "/leaderboard - Show the top inviters in the group\n"
    )
