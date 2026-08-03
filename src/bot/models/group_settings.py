"""
GroupSettings model — Per-group configuration.

Each group has exactly one settings record (1:1 relationship).
Settings control notification preferences, language, timezone,
and bot behavior within that specific group.

Created automatically when a group is registered with default values.
"""

from sqlalchemy import Boolean, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.core.enums import Language
from bot.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GroupSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Per-group bot configuration.

    All settings have sensible defaults and can be modified
    by the group owner or admins via the /settings command.
    """

    __tablename__ = "group_settings"

    # ==================== Foreign Key ====================
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        doc="The group this settings record belongs to.",
    )

    # ==================== Language ====================
    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default=Language.EN.value,
        server_default=text(f"'{Language.EN.value}'"),
        doc="Bot language for this group (en, uz, ru).",
    )

    # ==================== Timezone ====================
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
        server_default=text("'UTC'"),
        doc="IANA timezone for report generation (e.g., 'Asia/Tashkent').",
    )

    # ==================== Notification Preferences ====================
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
        doc="Master switch for all notifications in this group.",
    )

    join_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
        doc="Notify admins when a new member joins.",
    )

    leave_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Notify admins when a member leaves.",
    )

    milestone_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
        doc="Notify when invite milestones are reached (10, 25, 50, 100...).",
    )

    admin_change_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
        doc="Notify when admins are promoted or demoted.",
    )

    suspicious_activity_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
        doc="Notify when suspicious join patterns are detected.",
    )

    # ==================== Report Preferences ====================
    daily_report_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Automatically send daily invite reports.",
    )

    weekly_report_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Automatically send weekly invite reports.",
    )

    monthly_report_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Automatically send monthly invite reports.",
    )

    # ==================== Feature Flags ====================
    auto_generate_invite_links: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Auto-generate unique invite links for members who request one.",
    )

    track_public_joins: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
        doc="Track members who join via public username (no inviter attribution).",
    )

    # ==================== Relationships ====================
    group: Mapped["Group"] = relationship(  # noqa: F821
        "Group",
        back_populates="settings",
    )

    def __repr__(self) -> str:
        return (
            f"<GroupSettings(group_id={self.group_id}, "
            f"lang={self.language!r}, "
            f"tz={self.timezone!r})>"
        )
