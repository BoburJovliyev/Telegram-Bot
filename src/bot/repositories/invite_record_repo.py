"""
Invite Record Repository.
"""

from sqlalchemy import select, update, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.models.invite_record import InviteRecord
from bot.repositories.base import BaseRepository


class InviteRecordRepository(BaseRepository[InviteRecord]):
    """Data access layer for InviteRecord (the attribution table)."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InviteRecord, session)

    async def create_record(
        self,
        group_id: int,
        invitee_id: int,
        join_method: str,
        idempotency_key: str,
        inviter_id: int | None = None,
        invite_link_id: str | None = None,
        is_rejoin: bool = False,
    ) -> InviteRecord | None:
        """
        Create a new invite record.
        Uses ON CONFLICT DO NOTHING to prevent race conditions causing duplicates.
        Returns the created record, or None if it was a duplicate.
        """
        stmt = insert(InviteRecord).values(
            group_id=group_id,
            invitee_id=invitee_id,
            inviter_id=inviter_id,
            invite_link_id=invite_link_id,
            join_method=join_method,
            is_rejoin=is_rejoin,
            idempotency_key=idempotency_key,
        ).on_conflict_do_nothing(
            index_elements=["idempotency_key"]
        ).returning(InviteRecord)

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def mark_inactive(self, group_id: int, invitee_id: int) -> InviteRecord | None:
        """
        Mark an active invite record as inactive (user left).
        Returns the record if found, so services can decrement the inviter's stats.
        """
        stmt = (
            update(InviteRecord)
            .where(
                InviteRecord.group_id == group_id,
                InviteRecord.invitee_id == invitee_id,
                InviteRecord.is_active == True,
            )
            .values(
                is_active=False,
                left_at=select(text("NOW()")).scalar_subquery(),
                updated_at=select(text("NOW()")).scalar_subquery(),
            )
            .returning(InviteRecord)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def get_active_record(self, group_id: int, invitee_id: int) -> InviteRecord | None:
        """Get the currently active invite record for a user in a group."""
        stmt = (
            select(InviteRecord)
            .options(joinedload(InviteRecord.inviter))
            .where(
                InviteRecord.group_id == group_id,
                InviteRecord.invitee_id == invitee_id,
                InviteRecord.is_active == True,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
