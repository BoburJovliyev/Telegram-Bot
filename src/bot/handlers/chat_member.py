"""
Handlers for regular chat members (chat_member and chat_join_request).

This is the core of the invite tracking mechanism. It processes:
1. Members joining via public username/search
2. Members joining via invite links
3. Members being added by admins
4. Members joining via join requests
5. Members leaving or being kicked
"""

import time
import structlog
from aiogram import Bot, Router, F
from aiogram.filters.chat_member_updated import (
    IS_MEMBER,
    IS_NOT_MEMBER,
    ChatMemberUpdatedFilter,
)
from aiogram.types import ChatJoinRequest, ChatMemberUpdated, Message

from bot.core.enums import JoinMethod, MemberStatus
from bot.services.invite_service import InviteTrackingService

logger = structlog.get_logger(__name__)
router = Router(name="chat_member_router")


@router.chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER)
)
async def member_joined_group(
    event: ChatMemberUpdated,
    invite_service: InviteTrackingService,
) -> None:
    """
    Triggered when a normal user joins the group.
    Attempts to determine the join method (link, public, admin add).
    """
    # Ignore bots joining
    if event.new_chat_member.user.is_bot:
        return

    chat_id = event.chat.id
    user = event.new_chat_member.user
    idempotency_key = f"join_{chat_id}_{user.id}_{int(time.time())}"
    
    join_method = JoinMethod.UNKNOWN.value
    invite_link = None
    is_via_join_request = False
    inviter_user = None

    # 1. Check if joined via an Invite Link
    if event.invite_link:
        join_method = JoinMethod.INVITE_LINK.value
        invite_link = event.invite_link

    # 2. Check if added by an Administrator (from_user is different from the joined user)
    elif event.from_user.id != user.id:
        join_method = JoinMethod.ADMIN_ADDED.value
        inviter_user = event.from_user

    # 3. If no invite link and from_user == user, it's a public join (searched by username)
    elif event.from_user.id == user.id:
        join_method = JoinMethod.PUBLIC.value

    # Process via the service
    await invite_service.process_join(
        group_id=chat_id,
        user=user,
        join_method=join_method,
        invite_link=invite_link,
        idempotency_key=idempotency_key,
        is_via_join_request=is_via_join_request,
        inviter_user=inviter_user,
    )


@router.chat_join_request()
async def member_join_request(
    request: ChatJoinRequest,
    bot: Bot,
    invite_service: InviteTrackingService,
) -> None:
    """
    Triggered when a user requests to join via a specialized invite link.
    We process the join here, and then approve the request automatically.
    """
    chat_id = request.chat.id
    user = request.from_user
    idempotency_key = f"join_req_{chat_id}_{user.id}_{request.date.timestamp()}"

    await invite_service.process_join(
        group_id=chat_id,
        user=user,
        join_method=JoinMethod.JOIN_REQUEST.value,
        invite_link=request.invite_link,
        idempotency_key=idempotency_key,
        is_via_join_request=True,
    )

    # Automatically approve the request so they actually enter the group
    try:
        await bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
    except Exception as e:
        logger.error(
            "Failed to approve chat join request", 
            chat_id=chat_id, 
            user_id=user.id, 
            error=str(e)
        )


@router.chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER)
)
async def member_left_group(
    event: ChatMemberUpdated,
    invite_service: InviteTrackingService,
) -> None:
    """
    Triggered when a user leaves, is kicked, or banned.
    """
    # Ignore bots leaving
    if event.old_chat_member.user.is_bot:
        return

    chat_id = event.chat.id
    user = event.old_chat_member.user
    new_status = event.new_chat_member.status
    idempotency_key = f"leave_{chat_id}_{user.id}_{int(time.time())}"
    
    # Map Telegram status to our enum
    mapped_status = MemberStatus.LEFT.value
    if new_status == "kicked":
        mapped_status = MemberStatus.BANNED.value # 'kicked' means banned in TG
    elif new_status == "restricted" and not event.new_chat_member.is_member:
        # Sometimes restricted means they left depending on flags, usually 'left' is explicit
        pass

    await invite_service.process_leave(
        group_id=chat_id,
        user_id=user.id,
        status=mapped_status,
        idempotency_key=idempotency_key,
    )


@router.message(F.new_chat_members)
async def new_chat_members_handler(
    message: Message,
    invite_service: InviteTrackingService,
) -> None:
    """
    Fallback: Triggered when a normal user joins the group via service message.
    This ensures we track when a user directly adds another user, which often 
    generates a message instead of a chat_member update depending on privileges.
    """
    chat_id = message.chat.id
    
    if not message.new_chat_members:
        return
        
    for user in message.new_chat_members:
        if user.is_bot:
            continue
            
        idempotency_key = f"join_msg_{chat_id}_{user.id}_{int(message.date.timestamp())}"
        
        join_method = JoinMethod.UNKNOWN.value
        inviter_user = None
        
        # If the person who sent the message is not the person who joined, it's an admin/user add
        if message.from_user and message.from_user.id != user.id:
            join_method = JoinMethod.ADMIN_ADDED.value
            inviter_user = message.from_user
        elif message.from_user and message.from_user.id == user.id:
            join_method = JoinMethod.PUBLIC.value

        await invite_service.process_join(
            group_id=chat_id,
            user=user,
            join_method=join_method,
            invite_link=None,
            idempotency_key=idempotency_key,
            is_via_join_request=False,
            inviter_user=inviter_user,
        )
