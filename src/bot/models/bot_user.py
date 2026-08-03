"""
BotUser model — Global user registry.

Every Telegram user that the bot encounters (in any group) is
stored here. This is the canonical source for user metadata
across all groups.

This table uses Telegram's user_id as the natural primary key
(BigInteger) since it is globally unique and immutable.

Relationships:
- One user can be a member of many groups (via Member)
- One user can be an admin of many groups (via GroupAdmin)
- One user can own many groups (via Group.owner_id)
- One user can create many invite links (via InviteLink.creator_id)
- One user can have many invite records as inviter or invitee
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base, TimestampMixin


class BotUser(Base, TimestampMixin):
    """
    Global Telegram user record.

    Stores the latest known metadata for every user seen by the bot.
    Updated whenever the bot receives an update involving this user.
    """

    __tablename__ = "bot_users"

    # ==================== Primary Key ====================
    # Telegram user_id is a positive 64-bit integer.
    # Used as natural PK — no surrogate key needed.
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=False,
        doc="Telegram user ID (positive integer).",
    )

    # ==================== User Metadata ====================
    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Telegram username (without @), may change or be null.",
    )

    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        doc="User's first name as shown in Telegram.",
    )

    last_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="User's last name, may be null.",
    )

    language_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="IETF language tag from Telegram client (e.g., 'en', 'ru', 'uz').",
    )

    # ==================== Status Flags ====================
    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Whether the user has Telegram Premium.",
    )

    is_bot: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Whether this is a bot account.",
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Whether the Telegram account has been deleted.",
    )

    is_fake: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Whether this account is flagged as suspicious/fake.",
    )

    # ==================== Activity Tracking ====================
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        doc="Timestamp when the bot first encountered this user.",
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        doc="Timestamp of the most recent activity from this user.",
    )

    # ==================== Relationships ====================
    # Groups this user owns
    owned_groups: Mapped[list["Group"]] = relationship(  # noqa: F821
        "Group",
        back_populates="owner",
        lazy="selectin",
        foreign_keys="Group.owner_id",
    )

    # Memberships across all groups
    memberships: Mapped[list["Member"]] = relationship(  # noqa: F821
        "Member",
        back_populates="user",
        lazy="noload",
        foreign_keys="Member.user_id",
    )

    # Admin roles across all groups
    admin_roles: Mapped[list["GroupAdmin"]] = relationship(  # noqa: F821
        "GroupAdmin",
        back_populates="user",
        lazy="noload",
        foreign_keys="GroupAdmin.user_id",
    )

    # Invite links created by this user
    created_invite_links: Mapped[list["InviteLink"]] = relationship(  # noqa: F821
        "InviteLink",
        back_populates="creator",
        lazy="noload",
        foreign_keys="InviteLink.creator_id",
    )

    def __repr__(self) -> str:
        return (
            f"<BotUser(id={self.id}, "
            f"username={self.username!r}, "
            f"first_name={self.first_name!r})>"
        )

    @property
    def full_name(self) -> str:
        """Return the user's full display name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def mention(self) -> str:
        """Return a Telegram-compatible mention string."""
        if self.username:
            return f"@{self.username}"
        return self.full_name
