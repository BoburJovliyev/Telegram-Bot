"""
Group Service.

Handles the lifecycle of groups within the bot, including
when the bot is added, removed, and synchronizing admins.
"""

from typing import Any

from aiogram import Bot
from aiogram.types import Chat, User

from bot.core.enums import AdminRole
from bot.models.group import Group
from bot.services.base import BaseService


class GroupService(BaseService):
    """Business logic for group management."""

    async def register_or_update_group(
        self,
        chat: Chat,
        bot_member: User,
        adder: User | None = None,
    ) -> Group:
        """
        Register a new group or update an existing one when the bot joins.
        """
        self.logger.info(
            "Registering/Updating group", 
            chat_id=chat.id, 
            title=chat.title
        )

        async with self.uow as uow:
            # 1. Upsert Group (implicitly provisions GroupSettings)
            group = await uow.groups.upsert_group(
                chat_id=chat.id,
                title=chat.title or "Unknown Group",
                username=chat.username,
                description=chat.description,
            )

            # 2. Upsert the person who added the bot (if known)
            if adder:
                await uow.users.upsert_user(
                    user_id=adder.id,
                    first_name=adder.first_name,
                    username=adder.username,
                    last_name=adder.last_name,
                    language_code=adder.language_code,
                    is_premium=adder.is_premium or False,
                )

                # Make the adder a super admin in our DB by default
                await uow.admins.upsert_admin(
                    group_id=chat.id,
                    user_id=adder.id,
                    role=AdminRole.OWNER.value,
                    permissions={"can_promote_members": True, "can_restrict_members": True}
                )

            # 3. Log event
            await uow.events.log_event(
                group_id=chat.id,
                user_id=bot_member.id,
                event_type="bot_joined",
                idempotency_key=f"bot_joined_{chat.id}_{group.bot_joined_at.timestamp()}",
                performed_by_id=adder.id if adder else None,
            )

            await uow.commit()
            return group

    async def handle_bot_removed(self, chat_id: int, remover_id: int | None = None) -> None:
        """
        Handle the event when the bot is kicked or leaves a group.
        """
        self.logger.info("Bot removed from group", chat_id=chat_id)

        async with self.uow as uow:
            await uow.groups.mark_inactive(chat_id)
            
            # Note: We don't delete data, we soft-archive to maintain analytics
            
            await uow.events.log_event(
                group_id=chat_id,
                user_id=0, # Bot's perspective
                event_type="bot_removed",
                idempotency_key=f"bot_removed_{chat_id}",
                performed_by_id=remover_id,
            )
            
            await uow.commit()

    async def sync_administrators(self, bot: Bot, chat_id: int) -> int | None:
        """
        Fetch the current admin list from Telegram API and sync our database.
        Demotes admins in our DB who are no longer admins in Telegram.
        Returns the owner_id of the group if found.
        """
        self.logger.info("Syncing administrators", chat_id=chat_id)
        
        try:
            tg_admins = await bot.get_chat_administrators(chat_id)
        except Exception as e:
            self.logger.error("Failed to fetch administrators from Telegram", error=str(e))
            return None

        tg_admin_ids = {admin.user.id for admin in tg_admins}
        owner_id = None

        async with self.uow as uow:
            # 1. Get current active admins from our DB
            db_admins = await uow.admins.get_active_admins(chat_id)
            db_admin_ids = {admin.user_id for admin in db_admins}

            # 2. Find admins to demote (in DB but not in Telegram)
            to_demote = db_admin_ids - tg_admin_ids
            for user_id in to_demote:
                await uow.admins.demote_admin(chat_id, user_id)
                self.logger.debug("Admin demoted", user_id=user_id)

            # 3. Find admins to upsert
            for admin in tg_admins:
                if admin.user.is_bot:
                    continue
                    
                # Ensure user exists in our DB
                await uow.users.upsert_user(
                    user_id=admin.user.id,
                    first_name=admin.user.first_name,
                    username=admin.user.username,
                    last_name=admin.user.last_name,
                    language_code=admin.user.language_code,
                    is_bot=admin.user.is_bot
                )
                
                # Upsert admin record
                role = AdminRole.OWNER.value if admin.status == "creator" else AdminRole.ADMIN.value
                
                if admin.status == "creator":
                    owner_id = admin.user.id
                    await uow.groups.set_group_owner(chat_id, owner_id)
                
                # Extract boolean permissions based on Telegram's ChatMemberAdministrator properties
                permissions = {
                    "can_manage_chat": getattr(admin, "can_manage_chat", False),
                    "can_delete_messages": getattr(admin, "can_delete_messages", False),
                    "can_manage_video_chats": getattr(admin, "can_manage_video_chats", False),
                    "can_restrict_members": getattr(admin, "can_restrict_members", False),
                    "can_promote_members": getattr(admin, "can_promote_members", False),
                    "can_change_info": getattr(admin, "can_change_info", False),
                    "can_invite_users": getattr(admin, "can_invite_users", False),
                    "can_pin_messages": getattr(admin, "can_pin_messages", False),
                }

                await uow.admins.upsert_admin(
                    group_id=chat_id,
                    user_id=admin.user.id,
                    role=role,
                    custom_title=getattr(admin, "custom_title", None),
                    is_anonymous=getattr(admin, "is_anonymous", False),
                    permissions=permissions
                )
            
            await uow.commit()
            self.logger.info("Administrator sync complete", demoted=len(to_demote))
            return owner_id
