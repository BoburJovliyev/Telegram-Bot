"""
Basic command handlers.
"""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.models.member import Member
from bot.services.group_service import GroupService

router = Router(name="commands_router")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle the /start command."""
    if message.chat.type == "private":
        await message.answer(
            "👋 Assalomu alaykum! Bot faol va ishlamoqda. (The bot is up and running!)\n\n"
            "Welcome to the Enterprise Invite Tracker Bot!\n\n"
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
        "/admin - Open the admin dashboard\n"
    )

@router.message(Command("stats"))
async def cmd_stats(message: Message, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Handle the /stats command."""
    if message.chat.type == "private":
        await message.answer("❌ This command must be used in a group.")
        return

    async with session_factory() as session:
        stmt = select(Member).where(
            Member.group_id == message.chat.id,
            Member.user_id == message.from_user.id
        )
        member = (await session.execute(stmt)).scalar_one_or_none()

    if not member:
        await message.answer("You have not invited anyone yet.")
        return

    await message.answer(
        f"📊 <b>Your Invite Stats</b>\n\n"
        f"👥 Total Invited: <b>{member.total_invited}</b>\n"
        f"✅ Currently Active: <b>{member.active_invited}</b>"
    )

@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Handle the /leaderboard command."""
    if message.chat.type == "private":
        await message.answer("❌ This command must be used in a group.")
        return

    async with session_factory() as session:
        stmt = (
            select(Member)
            .where(Member.group_id == message.chat.id, Member.total_invited > 0)
            .order_by(Member.total_invited.desc())
            .limit(10)
        )
        members = (await session.execute(stmt)).scalars().all()

    if not members:
        await message.answer("No invites have been tracked yet.")
        return

    lines = ["🏆 <b>Top 10 Inviters</b>\n"]
    for i, member in enumerate(members, start=1):
        name = member.user.first_name if member.user else f"User {member.user_id}"
        lines.append(f"{i}. {name} — {member.total_invited} invites")

    from bot.keyboards.inline import get_pagination_keyboard
    
    await message.answer(
        "\n".join(lines),
        reply_markup=get_pagination_keyboard("leaderboard", 1, 1)
    )

@router.message(Command("hisobot"))
async def cmd_hisobot(message: Message) -> None:
    """Handle the /hisobot command."""
    if message.chat.type == "private":
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi.")
        return

    from bot.keyboards.report_keyboards import get_report_periods_keyboard
    
    await message.answer(
        "📊 <b>Hisobot davrini tanlang:</b>\n\n"
        "Qaysi davr uchun statistika ko'rmoqchisiz?",
        reply_markup=get_report_periods_keyboard()
    )
