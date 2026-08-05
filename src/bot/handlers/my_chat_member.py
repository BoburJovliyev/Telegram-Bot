"""
Handlers for bot's own membership status changes (my_chat_member).

Used to detect when the bot is added to a group (to register it)
or when it is kicked/leaves (to mark it inactive).
"""

import structlog
from aiogram import Bot, F, Router
from aiogram.filters.chat_member_updated import (
    IS_MEMBER,
    IS_NOT_MEMBER,
    PROMOTED_TRANSITION,
    ChatMemberUpdatedFilter,
)
from aiogram.types import ChatMemberUpdated

from bot.services.group_service import GroupService

logger = structlog.get_logger(__name__)
router = Router(name="my_chat_member_router")


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER)
)
async def bot_added_to_group(
    event: ChatMemberUpdated,
    bot: Bot,
    group_service: GroupService,
) -> None:
    """
    Triggered when the bot is added to a group as a regular member
    or as an administrator.
    """
    chat = event.chat
    adder = event.from_user
    bot_member = event.new_chat_member.user

    logger.info("Bot added to group", chat_id=chat.id, title=chat.title, adder_id=adder.id)

    # Register the group in the database
    await group_service.register_or_update_group(
        chat=chat,
        bot_member=bot_member,
        adder=adder,
    )

    # Sync admins immediately and get the owner_id
    owner_id = await group_service.sync_administrators(bot, chat.id)

    # Send a welcome message to the group
    await bot.send_message(
        chat.id,
        (
            "👋 Assalomu alaykum! Men guruh/kanalga qo'shildim.\n\n"
            "Mening vazifam shu guruh/kanalga kim qancha odam qo'shganini hisoblab borish. "
            "To'g'ri ishlashim uchun **menga Administrator huquqlarini (xususan 'Foydalanuvchilarni qo'shish' - Invite Users) berishingiz shart**.\n\n"
            "Nimalar qila olishimni ko'rish uchun /help buyrug'ini yuboring."
        ),
    )

    # Send a DM to the group owner in Uzbek
    if owner_id:
        try:
            await bot.send_message(
                owner_id,
                (
                    f"👋 Assalomu alaykum! Men sizning <b>{chat.title}</b> guruh/kanalingizga qo'shildim.\n\n"
                    "🤖 <b>Mening vazifalarim:</b>\n"
                    "• Guruh/kanalga kim qancha odam qo'shganini aniq hisoblab borish\n"
                    "• Havola (link) orqali qo'shilganlarni ham aniqlash\n"
                    "• Har 30 daqiqada sizga bugungi qo'shilgan a'zolar bo'yicha hisobot yuborish\n\n"
                    "✅ <b>Muhim eslatma:</b> To'liq ishlashim uchun guruh/kanalda menga <i>'Foydalanuvchilarni qo'shish' (Invite Users)</i> huquqini berishingiz so'raladi.\n\n"
                    "Guruh/kanalda /hisobot buyrug'i orqali istalgan vaqt statistikalarni ko'rishingiz mumkin."
                )
            )
        except Exception as e:
            logger.warning("Could not send welcome DM to group owner", owner_id=owner_id, error=str(e))


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER)
)
async def bot_removed_from_group(
    event: ChatMemberUpdated,
    group_service: GroupService,
) -> None:
    """
    Triggered when the bot is kicked or leaves a group.
    """
    chat = event.chat
    remover = event.from_user

    logger.info("Bot removed from group", chat_id=chat.id, remover_id=remover.id)

    # Mark the group as inactive in the database
    await group_service.handle_bot_removed(
        chat_id=chat.id,
        remover_id=remover.id,
    )


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=PROMOTED_TRANSITION)
)
async def bot_promoted_in_group(
    event: ChatMemberUpdated,
    bot: Bot,
    group_service: GroupService,
) -> None:
    """
    Triggered when the bot's administrator permissions are changed.
    """
    logger.info("Bot admin permissions changed", chat_id=event.chat.id)
    
    # Resync admins in case permissions changed things we care about
    await group_service.sync_administrators(bot, event.chat.id)
