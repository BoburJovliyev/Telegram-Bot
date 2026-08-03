"""
Daily Stats Repository.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.daily_stats import DailyStats
from bot.repositories.base import BaseRepository


class DailyStatsRepository(BaseRepository[DailyStats]):
    """Data access layer for DailyStats records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DailyStats, session)

    async def upsert_stats(self, group_id: int, stats_date: date, **kwargs) -> DailyStats:
        """
        Insert or update a daily stats record.
        """
        stmt = insert(DailyStats).values(
            group_id=group_id,
            stats_date=stats_date,
            **kwargs
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["group_id", "stats_date"],
            set_={k: getattr(stmt.excluded, k) for k in kwargs.keys()}
        ).returning(DailyStats)

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one()

    async def get_by_date(self, group_id: int, stats_date: date) -> DailyStats | None:
        """Get stats for a specific group and date."""
        stmt = select(DailyStats).where(
            DailyStats.group_id == group_id,
            DailyStats.stats_date == stats_date
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
