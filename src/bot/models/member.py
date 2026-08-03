"""
Member model — Per-group membership records.

Tracks the relationship between a user and a specific group.
One user can have multiple Member records (one per group they've been in).

This is where denormalized invite counters are stored:
- total_invited: lifetime count of users this member has invited
- active_invited: currently-active invited users
These are updated atomically when join/leave events occur.

The unique constraint on (group_id, user_id) ensures one active
record per user per group. Historical data is preserved via
MemberEvent and InviteRecord tables.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.core.enums import JoinMethod, MemberStatus
from bot.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Member(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Membership record for a user in a specific group.

    Represents the current state of a user's membership,
    including how they joined, who invited them, and their
    invite statistics.
    """

    __tablename__ = "members"

    # ==================== Foreign Keys ====================
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        doc="The group this membership belongs to.",
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("bot_users.id", ondelete="CASCADE"),
        nullable=False,
        doc="The member's Telegram user ID.",
    )

    # ==================== Join Information ====================
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MemberStatus.ACTIVE.value,
        doc="Current membership status: active, left, kicked, banned, restricted.",
    )

    join_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=JoinMethod.UNKNOWN.value,
        doc="How the user joined: invite_link, added_by_admin, join_request, public, unknown.",
    )

    # The invite link used to join (null if joined via public username or direct add)
    invite_link_id: Mapped[str | None] = mapped_column(
        ForeignKey("invite_links.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="The invite link used to join (null if not applicable).",
    )

    # Who invited this member (null if no inviter could be determined)
    invited_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("bot_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Telegram user ID of the person who invited this member.",
    )

    # ==================== Timestamps ====================
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        doc="When the user most recently joined the group.",
    )

    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the user last left/was removed (null if currently active).",
    )

    # ==================== Counters ====================
    rejoin_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Number of times this user has rejoined the group.",
    )

    ban_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Number of times this user has been banned.",
    )

    mute_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Number of times this user has been muted/restricted.",
    )

    warning_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Number of warnings issued to this user.",
    )

    # ==================== Invite Statistics (Denormalized) ====================
    # These counters are maintained atomically by the InviteTrackingService
    # and represent this member's effectiveness as an inviter.

    total_invited: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Lifetime total of users this member has invited to this group.",
    )

    active_invited: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Number of currently-active members that this member invited.",
    )

    # ==================== Flags ====================
    is_via_join_request: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Whether the user joined via a join request that was approved.",
    )

    # ==================== Relationships ====================
    group: Mapped["Group"] = relationship(  # noqa: F821
        "Group",
        back_populates="members",
    )

    user: Mapped["BotUser"] = relationship(  # noqa: F821
        "BotUser",
        back_populates="memberships",
        foreign_keys=[user_id],
    )

    inviter: Mapped["BotUser | None"] = relationship(  # noqa: F821
        "BotUser",
        foreign_keys=[invited_by_id],
        lazy="joined",
    )

    invite_link: Mapped["InviteLink | None"] = relationship(  # noqa: F821
        "InviteLink",
        lazy="joined",
    )

    invite_records_as_invitee: Mapped[list["InviteRecord"]] = relationship(  # noqa: F821
        "InviteRecord",
        back_populates="invitee_member",
        lazy="noload",
        foreign_keys="InviteRecord.invitee_id",
        primaryjoin="and_(Member.user_id == foreign(InviteRecord.invitee_id), "
        "Member.group_id == InviteRecord.group_id)",
        viewonly=True,
    )

    # ==================== Indexes ====================
    __table_args__ = (
        # Primary lookup: one record per user per group
        Index(
            "uq_members_group_user",
            "group_id",
            "user_id",
            unique=True,
        ),
        # Leaderboard query: top inviters for a group
        Index(
            "ix_members_group_total_invited",
            "group_id",
            "total_invited",
        ),
        # Filter by status within a group
        Index(
            "ix_members_group_status",
            "group_id",
            "status",
        ),
        # Find all members invited by a specific user
        Index(
            "ix_members_invited_by",
            "invited_by_id",
            "group_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Member(group={self.group_id}, "
            f"user={self.user_id}, "
            f"status={self.status!r}, "
            f"invited={self.total_invited})>"
        )

    @property
    def is_active(self) -> bool:
        """Check if the member is currently active in the group."""
        return self.status == MemberStatus.ACTIVE.value

    @property
    def left_invited_count(self) -> int:
        """
        Number of invited members who have since left the group.

        Calculated from the denormalized counters.
        """
        return max(0, self.total_invited - self.active_invited)

    @property
    def invite_retention_rate(self) -> float:
        """
        Retention rate of members invited by this user.

        Returns percentage (0-100) of invited members still active.
        """
        if self.total_invited == 0:
            return 0.0
        return (self.active_invited / self.total_invited) * 100
