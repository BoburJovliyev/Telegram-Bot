"""
InviteRecord model — The core tracking table: who invited whom.

This is the most critical table in the system. Each record represents
a single invitation event: one user (inviter) bringing another user
(invitee) into a group.

Design decisions:
- inviter_id is NULLABLE: public joins have no inviter
- is_active tracks whether the invitee is still in the group
- is_rejoin distinguishes first-time joins from rejoins
- The unique constraint (group_id, invitee_id, joined_at) prevents
  duplicate records for the same join event
- Separated from Member to allow multiple records per user (rejoins)
  while Member maintains the current state

Query patterns this table supports:
1. "How many people did user X invite?" → COUNT WHERE inviter_id=X AND is_active=TRUE
2. "Who invited user Y?" → SELECT WHERE invitee_id=Y ORDER BY joined_at DESC LIMIT 1
3. "Show all invites for link Z" → SELECT WHERE invite_link_id=Z
4. "Top inviters this month" → GROUP BY inviter_id WHERE joined_at >= start_of_month
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

from bot.core.enums import JoinMethod
from bot.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InviteRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Single invitation event record.

    Immutable after creation — status changes (user leaving)
    are reflected by updating is_active and left_at, but the
    core attribution data (inviter, invitee, link) never changes.
    """

    __tablename__ = "invite_records"

    # ==================== Foreign Keys ====================
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        doc="The group where this invitation occurred.",
    )

    # The person who did the inviting (null for public/unknown joins)
    inviter_id: Mapped[int | None] = mapped_column(
        ForeignKey("bot_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Telegram user ID of the inviter (null if unknown/public).",
    )

    # The person who was invited
    invitee_id: Mapped[int] = mapped_column(
        ForeignKey("bot_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Telegram user ID of the invited person.",
    )

    # The invite link used (null if not applicable)
    invite_link_id: Mapped[str | None] = mapped_column(
        ForeignKey("invite_links.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="The invite link used for this join (null if direct add or public).",
    )

    # ==================== Join Details ====================
    join_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=JoinMethod.UNKNOWN.value,
        doc="How the invitee joined: invite_link, added_by_admin, join_request, public.",
    )

    is_rejoin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        doc="Whether this was a rejoin (user had previously been in the group).",
    )

    # ==================== Activity Status ====================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
        doc="Whether the invitee is currently still in the group.",
    )

    # ==================== Timestamps ====================
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        doc="When the invitee joined the group via this invite.",
    )

    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the invitee left the group (null if still active).",
    )

    # ==================== Idempotency ====================
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        doc=(
            "Unique key to prevent duplicate records from race conditions. "
            "Format: '{group_id}:{invitee_id}:{timestamp_epoch}'"
        ),
    )

    # ==================== Relationships ====================
    inviter: Mapped["BotUser | None"] = relationship(  # noqa: F821
        "BotUser",
        foreign_keys=[inviter_id],
        lazy="joined",
    )

    invitee: Mapped["BotUser"] = relationship(  # noqa: F821
        "BotUser",
        foreign_keys=[invitee_id],
        lazy="joined",
    )

    invite_link: Mapped["InviteLink | None"] = relationship(  # noqa: F821
        "InviteLink",
        back_populates="invite_records",
        lazy="joined",
    )

    invitee_member: Mapped["Member | None"] = relationship(  # noqa: F821
        "Member",
        foreign_keys="[InviteRecord.invitee_id, InviteRecord.group_id]",
        primaryjoin="and_(InviteRecord.invitee_id == Member.user_id, "
        "InviteRecord.group_id == Member.group_id)",
        lazy="noload",
        viewonly=True,
    )

    # ==================== Indexes ====================
    __table_args__ = (
        # Primary query: "how many active invites does user X have in group Y?"
        Index(
            "ix_invite_records_inviter_active",
            "inviter_id",
            "group_id",
            "is_active",
        ),
        # Query: "who invited user Y in group Z?"
        Index(
            "ix_invite_records_invitee_group",
            "invitee_id",
            "group_id",
        ),
        # Query: "all invites for link L"
        Index(
            "ix_invite_records_link",
            "invite_link_id",
        ),
        # Time-based queries for reports: "all joins this month"
        Index(
            "ix_invite_records_group_joined",
            "group_id",
            "joined_at",
        ),
        # Prevent exact duplicate join events
        Index(
            "uq_invite_records_group_invitee_time",
            "group_id",
            "invitee_id",
            "joined_at",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<InviteRecord("
            f"group={self.group_id}, "
            f"inviter={self.inviter_id}, "
            f"invitee={self.invitee_id}, "
            f"method={self.join_method!r}, "
            f"active={self.is_active})>"
        )
