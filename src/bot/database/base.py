"""
SQLAlchemy declarative base and common model mixins.

Provides the `Base` class that all ORM models inherit from,
plus reusable mixins for timestamps, soft deletes, and other
cross-cutting concerns.

Design decisions:
- UUIDs as primary keys for internal records (non-Telegram entities)
- BigInteger for Telegram IDs (user_id, chat_id) which serve as natural PKs
- Server-side defaults for timestamps to ensure consistency
- All tables use explicit naming conventions for indexes and constraints
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, MetaData, text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)

# ==============================================================================
# Naming Convention
# ==============================================================================
# Explicit naming convention for all database constraints.
# This ensures Alembic auto-generates meaningful constraint names
# and prevents conflicts across different databases.

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# ==============================================================================
# Declarative Base
# ==============================================================================


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Features:
    - Explicit MetaData with naming convention for Alembic compatibility
    - All models inherit __repr__ for debugging
    - Common type_annotation_map for consistent column types
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # Map Python types to SQLAlchemy column types globally
    type_annotation_map = {
        int: BigInteger,  # Default int maps to BigInteger for Telegram IDs
        datetime: DateTime(timezone=True),  # All datetimes are timezone-aware
    }

    def __repr__(self) -> str:
        """Generate a developer-friendly representation of the model instance."""
        # Get primary key columns
        pk_columns = self.__table__.primary_key.columns
        pk_values = ", ".join(
            f"{col.name}={getattr(self, col.name, '?')}" for col in pk_columns
        )
        return f"<{self.__class__.__name__}({pk_values})>"


# ==============================================================================
# Mixins
# ==============================================================================


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.

    Both columns use server-side defaults:
    - created_at: set once on INSERT via database NOW()
    - updated_at: set on INSERT and updated on every UPDATE

    Using server_default ensures timestamps are set even for raw SQL inserts,
    and timezone=True ensures all timestamps are timezone-aware (stored as UTC).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
        doc="Timestamp when the record was created (UTC).",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Timestamp when the record was last updated (UTC).",
    )


class UUIDPrimaryKeyMixin:
    """
    Mixin that adds a UUID v4 primary key column.

    Used for internal records that don't have a natural Telegram ID
    (e.g., InviteRecord, MemberEvent, DailyStats, GroupSettings).

    The UUID is generated in Python rather than via server_default
    to ensure it's available immediately after object creation
    (before flush/commit).
    """

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4()),
        doc="UUID v4 primary key.",
    )
