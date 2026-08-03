"""
DailyStats model — Pre-aggregated daily statistics per group.

Rather than computing statistics from raw events every time a report
is requested, this table stores pre-computed daily aggregates.
This dramatically improves report generation performance.

The aggregation job (scheduled via APScheduler) runs every 30 minutes
and upserts records for the current day. At end of day, the record
is finalized.

The unique constraint on (group_id, date) ensures exactly one
stats record per group per day.
"""

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DailyStats(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Pre-aggregated daily statistics for a group.

    Updated periodically by the stats_aggregation background job.
    One record per group per day.
    """

    __tablename__ = "daily_stats"

    # ==================== Foreign Key ====================
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        doc="The group these stats belong to.",
    )

    # ==================== Date ====================
    stats_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="The date these statistics cover (UTC).",
    )

    # ==================== Join Statistics ====================
    joins_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Total members who joined on this day.",
    )

    leaves_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Total members who left on this day.",
    )

    kicks_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Total members who were kicked on this day.",
    )

    bans_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Total members who were banned on this day.",
    )

    # ==================== Join Method Breakdown ====================
    invite_link_joins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Members who joined via tracked invite links.",
    )

    admin_added_joins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Members who were added by admins.",
    )

    public_joins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Members who joined via public username/search.",
    )

    join_request_joins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Members who joined via approved join requests.",
    )

    unknown_joins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Members whose join method could not be determined.",
    )

    rejoin_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Members who rejoined on this day.",
    )

    # ==================== Member Counts ====================
    active_members_eod: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Snapshot of active member count at end of day.",
    )

    # ==================== Inviter Statistics ====================
    unique_inviters: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Number of unique users who successfully invited someone today.",
    )

    # ==================== Rates ====================
    retention_rate: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0.0,
        server_default=text("0.0"),
        doc="Percentage of members still active from previous day joins.",
    )

    net_growth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Net member change (joins - leaves - kicks).",
    )

    # ==================== Relationships ====================
    group: Mapped["Group"] = relationship(  # noqa: F821
        "Group",
        back_populates="daily_stats",
    )

    # ==================== Indexes ====================
    __table_args__ = (
        # Primary query: "stats for group X on date Y"
        Index(
            "uq_daily_stats_group_date",
            "group_id",
            "stats_date",
            unique=True,
        ),
        # Range query: "stats for group X from date A to B"
        Index(
            "ix_daily_stats_group_date_range",
            "group_id",
            "stats_date",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DailyStats("
            f"group={self.group_id}, "
            f"date={self.stats_date}, "
            f"joins={self.joins_count}, "
            f"leaves={self.leaves_count})>"
        )
