"""
Notification Repository.
"""

from typing import Sequence

from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.notification import Notification
from bot.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Data access layer for Notification delivery logs."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Notification, session)

    async def get_pending_notifications(self, max_retries: int = 3, limit: int = 50) -> Sequence[Notification]:
        """Get failed notifications that are eligible for retry."""
        stmt = (
            select(Notification)
            .where(
                Notification.is_sent == False,
                Notification.retry_count < max_retries
            )
            .order_by(Notification.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_sent(self, notification_id: str) -> None:
        """Mark a notification as successfully delivered."""
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(
                is_sent=True,
                sent_at=select(text("NOW()")).scalar_subquery()
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def increment_retry(self, notification_id: str, error_message: str | None = None) -> None:
        """Increment retry count after a failure."""
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(
                retry_count=Notification.retry_count + 1,
                error_message=error_message,
                updated_at=select(text("NOW()")).scalar_subquery()
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()
