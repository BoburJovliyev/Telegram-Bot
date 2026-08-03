"""
Notification model — Notification delivery log.

Tracks all notifications sent by the bot to admins, owners,
or the bot owner. Used for:
- Preventing duplicate notifications
- Audit trail of what was communicated
- Retry logic for failed sends
- Rate limiting notifications per group
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.core.enums import NotificationType
from bot.database.base import Base, UUIDPrimaryKeyMixin


class Notification(Base, UUIDPrimaryKeyMixin):
    """
    Notification delivery record.

    Each record represents a single notification sent (or attempted)
    to a specific user. Failed notifications can be retried.
    """

    __tablename__ = "notifications"

    # ==================== Foreign Keys ====================
    # group_id is nullable because some notifications are global
    # (e.g., system alerts to the bot owner)
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="The group this notification relates to (null for global).",
    )

    # The recipient of the notification
    user_id: Mapped[int] = mapped_column(
        ForeignKey("bot_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Telegram user ID of the notification recipient.",
    )

    # ==================== Notification Data ====================
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of notification (member_joined, milestone_reached, etc.).",
    )

    message_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="The notification message content that was sent.",
    )

    # ==================== Delivery Status ====================
    is_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Whether the notification was successfully delivered.",
    )

    retry_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Number of delivery attempts made.",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if delivery failed.",
    )

    # ==================== Timestamps ====================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
        doc="When the notification was created.",
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the notification was successfully sent.",
    )

    # ==================== Relationships ====================
    user: Mapped["BotUser"] = relationship(  # noqa: F821
        "BotUser",
    )

    # ==================== Indexes ====================
    __table_args__ = (
        # Query: "all notifications for a user"
        Index(
            "ix_notifications_user_type",
            "user_id",
            "notification_type",
        ),
        # Query: "recent notifications for a group"
        Index(
            "ix_notifications_group_created",
            "group_id",
            "created_at",
        ),
        # Query: "failed notifications that need retry"
        Index(
            "ix_notifications_pending",
            "is_sent",
            "retry_count",
            postgresql_where=text("is_sent = FALSE AND retry_count < 3"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Notification("
            f"user={self.user_id}, "
            f"type={self.notification_type!r}, "
            f"sent={self.is_sent})>"
        )
