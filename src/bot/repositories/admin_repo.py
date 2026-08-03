"""
Admin Repository.
"""

from typing import Sequence

from sqlalchemy import select, update, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.core.enums import AdminRole
from bot.models.admin import GroupAdmin
from bot.repositories.base import BaseRepository


class AdminRepository(BaseRepository[GroupAdmin]):
    """Data access layer for GroupAdmin records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(GroupAdmin, session)

    async def upsert_admin(
        self,
        group_id: int,
        user_id: int,
        role: str = AdminRole.ADMIN.value,
        custom_title: str | None = None,
        is_anonymous: bool = False,
        permissions: dict[str, bool] | None = None,
    ) -> GroupAdmin:
        """
        Insert or update an admin record. 
        Re-activates a previously demoted admin if they are promoted again.
        """
        if permissions is None:
            permissions = {}
            
        values = {
            "group_id": group_id,
            "user_id": user_id,
            "role": role,
            "custom_title": custom_title,
            "is_anonymous": is_anonymous,
            "is_active": True,
            **permissions
        }

        stmt = insert(GroupAdmin).values(**values)

        # On conflict (already an active admin, or was previously one)
        stmt = stmt.on_conflict_do_update(
            index_elements=["group_id", "user_id"],
            set_={
                "role": stmt.excluded.role,
                "custom_title": stmt.excluded.custom_title,
                "is_anonymous": stmt.excluded.is_anonymous,
                "is_active": True,
                "demoted_at": None,
                "updated_at": select(text("NOW()")).scalar_subquery(),
                **{k: getattr(stmt.excluded, k) for k in permissions.keys()}
            },
        ).returning(GroupAdmin)

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one()

    async def demote_admin(self, group_id: int, user_id: int) -> None:
        """Mark an admin as inactive (soft delete)."""
        stmt = (
            update(GroupAdmin)
            .where(
                GroupAdmin.group_id == group_id,
                GroupAdmin.user_id == user_id,
                GroupAdmin.is_active == True,
            )
            .values(
                is_active=False,
                demoted_at=select(text("NOW()")).scalar_subquery(),
                updated_at=select(text("NOW()")).scalar_subquery(),
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_active_admins(self, group_id: int) -> Sequence[GroupAdmin]:
        """Get all currently active admins for a group."""
        stmt = (
            select(GroupAdmin)
            .options(joinedload(GroupAdmin.user))
            .where(
                GroupAdmin.group_id == group_id,
                GroupAdmin.is_active == True,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
