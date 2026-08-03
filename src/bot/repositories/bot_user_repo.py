"""
BotUser Repository.
"""

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bot_user import BotUser
from bot.repositories.base import BaseRepository


class BotUserRepository(BaseRepository[BotUser]):
    """Data access layer for BotUser records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(BotUser, session)

    async def upsert_user(
        self,
        user_id: int,
        first_name: str,
        username: str | None = None,
        last_name: str | None = None,
        language_code: str | None = None,
        is_premium: bool = False,
        is_bot: bool = False,
    ) -> BotUser:
        """
        Insert a new user or update their metadata if they already exist.
        Uses PostgreSQL ON CONFLICT (id) DO UPDATE.
        """
        stmt = insert(BotUser).values(
            id=user_id,
            first_name=first_name,
            username=username,
            last_name=last_name,
            language_code=language_code,
            is_premium=is_premium,
            is_bot=is_bot,
        )

        # Update metadata when user is seen again
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "first_name": stmt.excluded.first_name,
                "username": stmt.excluded.username,
                "last_name": stmt.excluded.last_name,
                "language_code": stmt.excluded.language_code,
                "is_premium": stmt.excluded.is_premium,
                "last_seen_at": select(text("CURRENT_TIMESTAMP")).scalar_subquery(),
            },
        ).returning(BotUser)

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one()

    async def get_by_username(self, username: str) -> BotUser | None:
        """Look up a user by their @username (case-insensitive)."""
        clean_username = username.lstrip("@").lower()
        stmt = select(BotUser).where(BotUser.username.ilike(clean_username))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
