"""
Analytics Engine.

Contains the complex SQLAlchemy 2.0 select statements used to
calculate raw statistics from the InviteRecord and MemberEvent tables.
These queries are heavy and are typically run by background jobs.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import and_, func, select, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import JoinMethod
from bot.models.group import Group
from bot.models.invite_record import InviteRecord
from bot.models.member import Member


class AnalyticsEngine:
    """
    Performs data aggregation and statistical calculations.
    Does not use the UnitOfWork directly, operates on raw sessions
    for read-only analytical workloads.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def calculate_daily_stats(self, group_id: int, target_date: date) -> dict[str, int | float]:
        """
        Calculate all daily statistics for a specific group and date.
        """
        # Define the time window (UTC)
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)
        
        # 1. Total Joins & Join Methods Breakdown
        join_stmt = (
            select(
                func.count(InviteRecord.id).label("total"),
                func.sum(
                    func.cast(InviteRecord.join_method == JoinMethod.INVITE_LINK.value, func.integer())
                ).label("link_joins"),
                func.sum(
                    func.cast(InviteRecord.join_method == JoinMethod.ADMIN_ADDED.value, func.integer())
                ).label("admin_joins"),
                func.sum(
                    func.cast(InviteRecord.join_method == JoinMethod.PUBLIC.value, func.integer())
                ).label("public_joins"),
                func.sum(
                    func.cast(InviteRecord.join_method == JoinMethod.JOIN_REQUEST.value, func.integer())
                ).label("request_joins"),
                func.sum(
                    func.cast(InviteRecord.is_rejoin == True, func.integer())
                ).label("rejoins"),
            )
            .where(
                InviteRecord.group_id == group_id,
                InviteRecord.joined_at >= start_dt,
                InviteRecord.joined_at < end_dt,
            )
        )
        
        join_result = (await self.session.execute(join_stmt)).first()
        
        # 2. Leaves (Active records that were marked inactive today)
        leave_stmt = (
            select(func.count(InviteRecord.id))
            .where(
                InviteRecord.group_id == group_id,
                InviteRecord.is_active == False,
                InviteRecord.left_at >= start_dt,
                InviteRecord.left_at < end_dt,
            )
        )
        leaves_count = (await self.session.execute(leave_stmt)).scalar() or 0
        
        # 3. Unique Inviters (Users who successfully invited >= 1 person today)
        inviters_stmt = (
            select(func.count(func.distinct(InviteRecord.inviter_id)))
            .where(
                InviteRecord.group_id == group_id,
                InviteRecord.inviter_id.is_not(None),
                InviteRecord.joined_at >= start_dt,
                InviteRecord.joined_at < end_dt,
            )
        )
        unique_inviters = (await self.session.execute(inviters_stmt)).scalar() or 0
        
        # 4. Total Active Members (Snapshot)
        active_stmt = (
            select(func.count(Member.user_id))
            .where(
                Member.group_id == group_id,
                Member.status == "active"
            )
        )
        active_members_eod = (await self.session.execute(active_stmt)).scalar() or 0

        # Calculate retention rate (percentage of today's joins that are still active)
        total_joins = join_result.total if join_result else 0
        
        retention_rate = 0.0
        if total_joins > 0:
            still_active_stmt = (
                select(func.count(InviteRecord.id))
                .where(
                    InviteRecord.group_id == group_id,
                    InviteRecord.joined_at >= start_dt,
                    InviteRecord.joined_at < end_dt,
                    InviteRecord.is_active == True
                )
            )
            still_active = (await self.session.execute(still_active_stmt)).scalar() or 0
            retention_rate = round((still_active / total_joins) * 100.0, 2)
            
        net_growth = total_joins - leaves_count

        return {
            "joins_count": total_joins,
            "leaves_count": leaves_count,
            "invite_link_joins": join_result.link_joins or 0,
            "admin_added_joins": join_result.admin_joins or 0,
            "public_joins": join_result.public_joins or 0,
            "join_request_joins": join_result.request_joins or 0,
            "rejoin_count": join_result.rejoins or 0,
            "unique_inviters": unique_inviters,
            "active_members_eod": active_members_eod,
            "retention_rate": retention_rate,
            "net_growth": net_growth,
        }
