"""
Group Repository.
"""

from typing import Sequence

from sqlalchemy import select, update, text
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models.group import Group
from bot.models.group_settings import GroupSettings
from bot.repositories.base import BaseRepository


class GroupRepository(BaseRepository[Group]):
    """Data access layer for Group and GroupSettings records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Group, session)

    async def upsert_group(
        self,
        chat_id: int,
        title: str,
        username: str | None = None,
        description: str | None = None,
    ) -> Group:
        """
        Insert a new group or update existing metadata.
        Automatically provisions default GroupSettings on insert.
        """
        stmt = insert(Group).values(
            id=chat_id,
            title=title,
            username=username,
            description=description,
            is_active=True,
            is_public=username is not None,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "title": stmt.excluded.title,
                "username": stmt.excluded.username,
                "description": stmt.excluded.description,
                "is_active": True,
                "is_public": stmt.excluded.username != None,
                "bot_joined_at": select(text("CURRENT_TIMESTAMP")).scalar_subquery(),
                "bot_left_at": None,
            },
        ).returning(Group)

        result = await self.session.execute(stmt)
        group = result.scalar_one()

        # Ensure settings exist
        settings_stmt = select(GroupSettings).where(GroupSettings.group_id == chat_id)
        settings_result = await self.session.execute(settings_stmt)
        if not settings_result.scalar_one_or_none():
            self.session.add(GroupSettings(group_id=chat_id))

        await self.session.flush()
        return group

    async def get_with_settings(self, chat_id: int) -> Group | None:
        """Retrieve a group eager-loaded with its settings."""
        stmt = select(Group).options(selectinload(Group.settings)).where(Group.id == chat_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_inactive(self, chat_id: int) -> None:
        """Mark a group as inactive (bot was kicked/left)."""
        stmt = (
            update(Group)
            .where(Group.id == chat_id)
            .values(
                is_active=False,
                bot_left_at=select(text("CURRENT_TIMESTAMP")).scalar_subquery()
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_active_groups(self) -> Sequence[Group]:
        """Retrieve all currently active groups."""
        stmt = select(Group).where(Group.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()
