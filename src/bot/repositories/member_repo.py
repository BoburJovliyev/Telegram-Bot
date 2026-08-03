"""
Member Repository.
"""

from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.core.enums import MemberStatus
from bot.models.member import Member
from bot.repositories.base import BaseRepository


class MemberRepository(BaseRepository[Member]):
    """Data access layer for Member records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Member, session)

    async def upsert_member(
        self,
        group_id: int,
        user_id: int,
        status: str = MemberStatus.ACTIVE.value,
        join_method: str | None = None,
        invite_link_id: str | None = None,
        invited_by_id: int | None = None,
        is_via_join_request: bool = False,
    ) -> Member:
        """
        Insert or update a group member's record.
        Handles rejoins and status changes correctly.
        """
        values = {
            "group_id": group_id,
            "user_id": user_id,
            "status": status,
            "is_via_join_request": is_via_join_request,
        }
        
        # Only set these on initial creation, preserve existing on update
        # unless explicitly provided in the upsert
        if join_method:
            values["join_method"] = join_method
        if invite_link_id:
            values["invite_link_id"] = invite_link_id
        if invited_by_id:
            values["invited_by_id"] = invited_by_id

        stmt = insert(Member).values(**values)

        update_set = {
            "status": stmt.excluded.status,
            "is_via_join_request": stmt.excluded.is_via_join_request,
            "updated_at": select(text("CURRENT_TIMESTAMP")).scalar_subquery(),
        }

        # Track rejoin logic
        if status == MemberStatus.ACTIVE.value:
            update_set["left_at"] = None
            # Only increment rejoin count if they were previously not active
            update_set["rejoin_count"] = Member.rejoin_count + 1
            update_set["joined_at"] = select(text("CURRENT_TIMESTAMP")).scalar_subquery()
            
            # Update attribution if new attribution is provided on rejoin
            if join_method:
                update_set["join_method"] = stmt.excluded.join_method
            if invite_link_id:
                update_set["invite_link_id"] = stmt.excluded.invite_link_id
            if invited_by_id:
                update_set["invited_by_id"] = stmt.excluded.invited_by_id
                
        elif status in (MemberStatus.LEFT.value, MemberStatus.KICKED.value, MemberStatus.BANNED.value):
            update_set["left_at"] = select(text("CURRENT_TIMESTAMP")).scalar_subquery()
            if status == MemberStatus.BANNED.value:
                update_set["ban_count"] = Member.ban_count + 1

        stmt = stmt.on_conflict_do_update(
            index_elements=["group_id", "user_id"],
            set_=update_set,
            # Prevent incrementing rejoin_count if they are already ACTIVE
            where=(
                (Member.status != MemberStatus.ACTIVE.value) 
                if status == MemberStatus.ACTIVE.value 
                else True
            )
        ).returning(Member)

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one()

    async def get_member(self, group_id: int, user_id: int) -> Member | None:
        """Retrieve a specific member eager-loaded with inviter and user info."""
        stmt = (
            select(Member)
            .options(
                joinedload(Member.user),
                joinedload(Member.inviter)
            )
            .where(
                Member.group_id == group_id,
                Member.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_invite_counters(
        self, group_id: int, user_id: int, active_only: bool = False
    ) -> None:
        """
        Atomically increment invite counters for an inviter.
        If active_only is True, only increments active_invited.
        """
        values = {"active_invited": Member.active_invited + 1}
        if not active_only:
            values["total_invited"] = Member.total_invited + 1
            
        stmt = (
            update(Member)
            .where(Member.group_id == group_id, Member.user_id == user_id)
            .values(**values)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def decrement_active_invited(self, group_id: int, user_id: int) -> None:
        """
        Atomically decrement active_invited counter (prevents negative values).
        Called when a user's invitee leaves the group.
        """
        stmt = (
            update(Member)
            .where(
                Member.group_id == group_id, 
                Member.user_id == user_id,
                Member.active_invited > 0
            )
            .values(active_invited=Member.active_invited - 1)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_top_inviters(
        self, group_id: int, limit: int = 10
    ) -> Sequence[Member]:
        """Get the leaderboard of top inviters in a group."""
        stmt = (
            select(Member)
            .options(joinedload(Member.user))
            .where(Member.group_id == group_id, Member.total_invited > 0)
            .order_by(Member.total_invited.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
