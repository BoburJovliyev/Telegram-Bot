"""
GroupAdmin model — Admin registry per group.

Tracks all administrators (including the owner) for every group
the bot is in. Automatically updated when the bot detects admin
changes via ChatMemberUpdated events.

Design notes:
- A user can be admin of multiple groups.
- When an admin is demoted, is_active is set to False and demoted_at
  is recorded (soft archive, not deleted) for audit trail.
- Permissions are stored individually to detect permission changes.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.core.enums import AdminRole
from bot.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GroupAdmin(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Administrator record for a specific group.

    Stores role, permissions, and activity timestamps.
    Historical records are kept (is_active=False) for audit purposes.
    """

    __tablename__ = "group_admins"

    # ==================== Foreign Keys ====================
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        doc="The group this admin belongs to.",
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("bot_users.id", ondelete="CASCADE"),
        nullable=False,
        doc="The admin's Telegram user ID.",
    )

    # ==================== Role ====================
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AdminRole.ADMIN.value,
        doc="Admin role: 'owner', 'admin', or 'moderator'.",
    )

    custom_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Custom admin title (e.g., 'Community Manager').",
    )

    # ==================== Telegram Permissions ====================
    # Individual permission flags from Telegram's ChatMemberAdministrator.
    # Stored separately to detect granular permission changes.

    can_manage_chat: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Can manage chat (general admin access).",
    )

    can_post_messages: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Can post messages in channels.",
    )

    can_edit_messages: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Can edit messages in channels.",
    )

    can_delete_messages: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Can delete other users' messages.",
    )

    can_restrict_members: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Can restrict/unrestrict/ban/unban members.",
    )

    can_promote_members: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Can promote/demote other admins.",
    )

    can_change_info: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Can change group info (title, photo, description).",
    )

    can_invite_users: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Can invite users and manage invite links.",
    )

    can_pin_messages: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Can pin messages.",
    )

    can_manage_video_chats: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Can manage video chats.",
    )

    # ==================== Status ====================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
        doc="Whether the admin is currently active (False = demoted).",
    )

    is_anonymous: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Whether the admin's identity is hidden in the group.",
    )

    # ==================== Timestamps ====================
    promoted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        doc="When this user was promoted to admin.",
    )

    demoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When this admin was demoted (null if still active).",
    )

    # ==================== Relationships ====================
    group: Mapped["Group"] = relationship(  # noqa: F821
        "Group",
        back_populates="admins",
    )

    user: Mapped["BotUser"] = relationship(  # noqa: F821
        "BotUser",
        back_populates="admin_roles",
    )

    # ==================== Indexes ====================
    __table_args__ = (
        # Fast lookup: "who are the active admins of this group?"
        Index("ix_group_admins_group_active", "group_id", "is_active"),
        # Fast lookup: "is this user an admin of this group?"
        Index("ix_group_admins_user_group", "user_id", "group_id"),
        # Uniqueness: one active record per user per group
        Index(
            "uq_group_admins_active_user_group",
            "group_id",
            "user_id",
            unique=True,
            sqlite_where=text("is_active = TRUE"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<GroupAdmin(group={self.group_id}, "
            f"user={self.user_id}, "
            f"role={self.role!r}, "
            f"active={self.is_active})>"
        )
