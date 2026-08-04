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

    # Sync admins immediately
    await group_service.sync_administrators(bot, chat.id)

    # Send a welcome message
    await bot.send_message(
        chat.id,
        (
            "👋 Hello! I am the Invite Tracker Bot.\n\n"
            "I'm now monitoring this group. To track invites accurately, "
            "<b>I must be an administrator with the 'Invite Users' permission.</b>\n\n"
            "If I was added by a normal user, please promote me to admin. "
            "Type /help to see what I can do."
        ),
    )


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
