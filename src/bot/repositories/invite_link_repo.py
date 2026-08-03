"""
Invite Link Repository.
"""

from datetime import datetime

from sqlalchemy import select, update, text
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.models.invite_link import InviteLink
from bot.repositories.base import BaseRepository


class InviteLinkRepository(BaseRepository[InviteLink]):
    """Data access layer for InviteLink records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InviteLink, session)

    async def upsert_link(
        self,
        group_id: int,
        creator_id: int,
        link_url: str,
        name: str | None = None,
        expire_date: datetime | None = None,
        member_limit: int | None = None,
        creates_join_request: bool = False,
        is_primary: bool = False,
        is_revoked: bool = False,
        is_bot_generated: bool = False,
    ) -> InviteLink:
        """
        Insert or update a tracked invite link.
        """
        stmt = insert(InviteLink).values(
            group_id=group_id,
            creator_id=creator_id,
            link_url=link_url,
            name=name,
            expire_date=expire_date,
            member_limit=member_limit,
            creates_join_request=creates_join_request,
            is_primary=is_primary,
            is_revoked=is_revoked,
            is_bot_generated=is_bot_generated,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["link_url"],
            set_={
                "name": stmt.excluded.name,
                "expire_date": stmt.excluded.expire_date,
                "member_limit": stmt.excluded.member_limit,
                "creates_join_request": stmt.excluded.creates_join_request,
                "is_primary": stmt.excluded.is_primary,
                "is_revoked": stmt.excluded.is_revoked,
                "revoked_at": select(text("CURRENT_TIMESTAMP")).scalar_subquery() if is_revoked else None,
                "updated_at": select(text("CURRENT_TIMESTAMP")).scalar_subquery(),
            },
        ).returning(InviteLink)

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one()

    async def get_by_url(self, link_url: str) -> InviteLink | None:
        """Look up an invite link by its URL."""
        stmt = (
            select(InviteLink)
            .options(joinedload(InviteLink.creator))
            .where(InviteLink.link_url == link_url)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_usage(self, link_id: str) -> None:
        """Atomically increment the tracked usage count."""
        stmt = (
            update(InviteLink)
            .where(InviteLink.id == link_id)
            .values(
                tracked_usage_count=InviteLink.tracked_usage_count + 1,
                active_usage_count=InviteLink.active_usage_count + 1,
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def decrement_active_usage(self, link_id: str) -> None:
        """Atomically decrement active usage when a member leaves."""
        stmt = (
            update(InviteLink)
            .where(InviteLink.id == link_id, InviteLink.active_usage_count > 0)
            .values(active_usage_count=InviteLink.active_usage_count - 1)
        )
        await self.session.execute(stmt)
        await self.session.flush()
