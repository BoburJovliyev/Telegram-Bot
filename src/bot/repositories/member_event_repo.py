"""
Member Event Repository.
"""

from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.member_event import MemberEvent
from bot.repositories.base import BaseRepository


class MemberEventRepository(BaseRepository[MemberEvent]):
    """Data access layer for the immutable MemberEvent audit log."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(MemberEvent, session)

    async def log_event(
        self,
        group_id: int,
        user_id: int,
        event_type: str,
        idempotency_key: str,
        performed_by_id: int | None = None,
        invite_link_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemberEvent | None:
        """
        Record a new event.
        Uses ON CONFLICT DO NOTHING to prevent duplicate events.
        """
        stmt = insert(MemberEvent).values(
            group_id=group_id,
            user_id=user_id,
            event_type=event_type,
            idempotency_key=idempotency_key,
            performed_by_id=performed_by_id,
            invite_link_id=invite_link_id,
            metadata=metadata,
        ).on_conflict_do_nothing(
            index_elements=["idempotency_key"]
        ).returning(MemberEvent)

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()
