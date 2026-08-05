"""
Invite Tracking Service.

The core engine for tracking how members join groups, attributing
the invite to the correct user, and updating statistics safely.
"""

from aiogram.types import ChatInviteLink, User

from bot.core.enums import JoinMethod, MemberStatus
from bot.services.base import BaseService


class InviteTrackingService(BaseService):
    """Core logic for tracking and attributing group joins."""

    async def process_join(
        self,
        group_id: int,
        user: User,
        join_method: str = JoinMethod.UNKNOWN.value,
        invite_link: ChatInviteLink | None = None,
        idempotency_key: str = "",
        is_via_join_request: bool = False,
        inviter_user: User | None = None,
    ) -> None:
        """
        Process a user joining the group and attribute the invite.
        """
        self.logger.info(
            "Processing join", 
            group_id=group_id, 
            user_id=user.id, 
            method=join_method
        )

        async with self.uow as uow:
            # 1. Ensure user exists in our DB
            await uow.users.upsert_user(
                user_id=user.id,
                first_name=user.first_name,
                username=user.username,
                last_name=user.last_name,
                language_code=user.language_code,
                is_premium=user.is_premium or False,
                is_bot=user.is_bot,
            )

            # 2. Check if this is a rejoin (does an active/inactive record exist?)
            existing_member = await uow.members.get_member(group_id, user.id)
            is_rejoin = existing_member is not None and existing_member.status != MemberStatus.ACTIVE.value
            
            # If they are already active and this is processed again, it might be a duplicate event
            if existing_member and existing_member.status == MemberStatus.ACTIVE.value:
                self.logger.warning("Join event for already active member", user_id=user.id)
                # We still proceed to ensure idempotency handles it safely

            # 3. Track Link Usage
            inviter_id = None
            link_id_str = None
            
            if invite_link:
                # Upsert the link to ensure we track it
                creator_id = invite_link.creator.id
                inviter_id = creator_id
                link_url = invite_link.invite_link
                
                db_link = await uow.invite_links.upsert_link(
                    group_id=group_id,
                    creator_id=creator_id,
                    link_url=link_url,
                    name=invite_link.name,
                    expire_date=invite_link.expire_date,
                    member_limit=invite_link.member_limit,
                    creates_join_request=invite_link.creates_join_request,
                    is_primary=invite_link.is_primary,
                    is_revoked=invite_link.is_revoked,
                )
                
                link_id_str = str(db_link.id)
                
                # Only increment usage if it's not a duplicate
                await uow.invite_links.increment_usage(link_id_str)
            elif inviter_user:
                # Added by another user
                inviter_id = inviter_user.id
                await uow.users.upsert_user(
                    user_id=inviter_user.id,
                    first_name=inviter_user.first_name,
                    username=inviter_user.username,
                    last_name=inviter_user.last_name,
                    language_code=inviter_user.language_code,
                    is_premium=inviter_user.is_premium or False,
                    is_bot=inviter_user.is_bot,
                )

            # 4. Create the Attribution Record
            record = await uow.invite_records.create_record(
                group_id=group_id,
                invitee_id=user.id,
                join_method=join_method,
                idempotency_key=idempotency_key,
                inviter_id=inviter_id,
                invite_link_id=link_id_str,
                is_rejoin=is_rejoin,
            )

            if record is None:
                # Idempotency triggered - we already processed this exact join
                self.logger.info("Duplicate join event skipped", idempotency_key=idempotency_key)
                return

            # 5. Upsert Member status
            await uow.members.upsert_member(
                group_id=group_id,
                user_id=user.id,
                status=MemberStatus.ACTIVE.value,
                join_method=join_method,
                invite_link_id=link_id_str,
                invited_by_id=inviter_id,
                is_via_join_request=is_via_join_request,
            )

            # 6. Increment Inviter's Statistics
            if inviter_id:
                # If they rejoined, and they were previously invited by someone else,
                # we don't give the 'total_invited' credit again (to prevent gaming),
                # but we do increment 'active_invited'.
                active_only = is_rejoin
                await uow.members.increment_invite_counters(
                    group_id=group_id,
                    user_id=inviter_id,
                    active_only=active_only
                )

            # 7. Write to immutable audit log
            await uow.events.log_event(
                group_id=group_id,
                user_id=user.id,
                event_type="joined",
                idempotency_key=f"event_{idempotency_key}",
                invite_link_id=link_id_str,
                event_metadata={"method": join_method, "is_rejoin": is_rejoin}
            )

            # 8. Commit the entire transaction atomically
            await uow.commit()
            self.logger.info("Join processed successfully", user_id=user.id)

    async def process_leave(
        self,
        group_id: int,
        user_id: int,
        status: str = MemberStatus.LEFT.value,
        idempotency_key: str = "",
    ) -> None:
        """
        Process a user leaving (or being kicked/banned) and decrement active counts.
        """
        self.logger.info(
            "Processing leave", 
            group_id=group_id, 
            user_id=user_id, 
            status=status
        )

        async with self.uow as uow:
            # 1. Update Member status
            await uow.members.upsert_member(
                group_id=group_id,
                user_id=user_id,
                status=status,
            )

            # 2. Mark the active invite record as inactive and get it
            record = await uow.invite_records.mark_inactive(group_id, user_id)
            
            if record:
                # 3. Decrement Inviter's active_invited count
                if record.inviter_id:
                    await uow.members.decrement_active_invited(group_id, record.inviter_id)
                    
                # 4. Decrement InviteLink's active_usage count
                if record.invite_link_id:
                    await uow.invite_links.decrement_active_usage(record.invite_link_id)

            # 5. Log the event
            await uow.events.log_event(
                group_id=group_id,
                user_id=user_id,
                event_type=status,
                idempotency_key=idempotency_key,
            )

            await uow.commit()
            self.logger.info("Leave processed successfully", user_id=user_id)
