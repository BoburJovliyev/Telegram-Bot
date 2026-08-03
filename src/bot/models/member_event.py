"""
MemberEvent model — Audit log of all member events.

Every significant event that occurs in a group is recorded here.
This table is append-only (no updates or deletes) and serves as
a complete audit trail for debugging, analytics, and compliance.

Events include: joins, leaves, kicks, bans, promotions, demotions,
mutes, warnings, and bot lifecycle events.

The idempotency_key prevents duplicate events from being recorded
when the same Telegram update is processed multiple times
(e.g., due to webhook retries or bot restarts).
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.core.enums import EventType
from bot.database.base import Base, UUIDPrimaryKeyMixin


class MemberEvent(Base, UUIDPrimaryKeyMixin):
    """
    Immutable audit log entry for a group member event.

    Once created, these records are never modified or deleted.
    They form the complete event history for analytics and auditing.
    """

    __tablename__ = "member_events"

    # ==================== Foreign Keys ====================
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        doc="The group where this event occurred.",
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("bot_users.id", ondelete="CASCADE"),
        nullable=False,
        doc="The user this event is about.",
    )

    # ==================== Event Data ====================
    event_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        doc="Type of event (join, leave, kick, ban, promote, etc.).",
    )

    # Who performed the action (null for self-initiated events like leaving)
    performed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("bot_users.id", ondelete="SET NULL"),
        nullable=True,
        doc="Who triggered this event (null for self-initiated actions).",
    )

    # Optional: the invite link involved (for join events)
    invite_link_id: Mapped[str | None] = mapped_column(
        ForeignKey("invite_links.id", ondelete="SET NULL"),
        nullable=True,
        doc="Invite link involved in this event (for join events).",
    )

    # ==================== Metadata ====================
    # Flexible JSON field for event-specific data that doesn't
    # warrant its own column. Examples:
    # - For bans: {"reason": "spam", "until_date": "2024-01-01"}
    # - For promotes: {"old_role": "member", "new_role": "admin"}
    # - For joins: {"join_method": "invite_link", "inviter_id": 123456}
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Event-specific metadata as JSON.",
    )

    # ==================== Idempotency ====================
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        doc=(
            "Unique key to prevent duplicate event records. "
            "Format: '{event_type}:{group_id}:{user_id}:{timestamp_epoch}'"
        ),
    )

    # ==================== Timestamp ====================
    # Using a dedicated created_at instead of TimestampMixin because
    # this table is append-only (no updated_at needed).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
        doc="When this event was recorded.",
    )

    # ==================== Relationships ====================
    group: Mapped["Group"] = relationship(  # noqa: F821
        "Group",
        back_populates="events",
    )

    user: Mapped["BotUser"] = relationship(  # noqa: F821
        "BotUser",
        foreign_keys=[user_id],
    )

    performed_by: Mapped["BotUser | None"] = relationship(  # noqa: F821
        "BotUser",
        foreign_keys=[performed_by_id],
    )

    invite_link: Mapped["InviteLink | None"] = relationship(  # noqa: F821
        "InviteLink",
    )

    # ==================== Indexes ====================
    __table_args__ = (
        # Primary query: "all events for a user in a group"
        Index(
            "ix_member_events_group_user",
            "group_id",
            "user_id",
        ),
        # Filter by event type: "all joins in this group"
        Index(
            "ix_member_events_group_type",
            "group_id",
            "event_type",
        ),
        # Time-based analytics: "events in this group today"
        Index(
            "ix_member_events_group_created",
            "group_id",
            "created_at",
        ),
        # Combined: "all join events in this group this month"
        Index(
            "ix_member_events_group_type_created",
            "group_id",
            "event_type",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MemberEvent("
            f"group={self.group_id}, "
            f"user={self.user_id}, "
            f"type={self.event_type!r}, "
            f"at={self.created_at})>"
        )
