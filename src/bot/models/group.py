"""
Group model — Registered Telegram groups.

Every group that the bot is added to gets registered here.
The Telegram chat_id (negative BigInteger for supergroups) is
used as the natural primary key.

Relationships:
- One group has one owner (FK -> BotUser)
- One group has many admins (via GroupAdmin)
- One group has many members (via Member)
- One group has many invite links (via InviteLink)
- One group has one settings record (via GroupSettings, 1:1)
- One group has many member events (via MemberEvent)
- One group has many daily stats (via DailyStats)
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base, TimestampMixin


class Group(Base, TimestampMixin):
    """
    Registered Telegram group/supergroup.

    Stores group metadata, ownership, and status information.
    The bot must be an administrator in the group to function.
    """

    __tablename__ = "groups"

    # ==================== Primary Key ====================
    # Telegram chat_id for supergroups is a negative 64-bit integer.
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=False,
        doc="Telegram chat ID (negative for supergroups).",
    )

    # ==================== Group Metadata ====================
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Group title as shown in Telegram.",
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Public group username (without @), null for private groups.",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Group description text.",
    )

    # The primary invite link exported by Telegram
    primary_invite_link: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        doc="Primary invite link from exportChatInviteLink.",
    )

    # ==================== Ownership ====================
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("bot_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Telegram user ID of the group owner/creator.",
    )

    # ==================== Statistics (denormalized for performance) ====================
    member_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Approximate total member count (synced periodically).",
    )

    tracked_member_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Number of members tracked by the bot in this group.",
    )

    # ==================== Status Flags ====================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
        doc="Whether the bot is currently active in this group.",
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Whether the group has a public username.",
    )

    # ==================== Timestamps ====================
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
        doc="When the bot was first added to this group.",
    )

    bot_joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
        doc="When the bot was most recently added to this group.",
    )

    bot_left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the bot was removed from this group (null if active).",
    )

    # ==================== Relationships ====================
    owner: Mapped["BotUser | None"] = relationship(  # noqa: F821
        "BotUser",
        back_populates="owned_groups",
        lazy="joined",
        foreign_keys=[owner_id],
    )

    settings: Mapped["GroupSettings | None"] = relationship(  # noqa: F821
        "GroupSettings",
        back_populates="group",
        lazy="joined",
        uselist=False,
        cascade="all, delete-orphan",
    )

    admins: Mapped[list["GroupAdmin"]] = relationship(  # noqa: F821
        "GroupAdmin",
        back_populates="group",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    members: Mapped[list["Member"]] = relationship(  # noqa: F821
        "Member",
        back_populates="group",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    invite_links: Mapped[list["InviteLink"]] = relationship(  # noqa: F821
        "InviteLink",
        back_populates="group",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    events: Mapped[list["MemberEvent"]] = relationship(  # noqa: F821
        "MemberEvent",
        back_populates="group",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    daily_stats: Mapped[list["DailyStats"]] = relationship(  # noqa: F821
        "DailyStats",
        back_populates="group",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Group(id={self.id}, "
            f"title={self.title!r}, "
            f"active={self.is_active})>"
        )
