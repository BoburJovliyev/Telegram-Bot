"""
Unit of Work Pattern.

Encapsulates database transactions and manages the lifecycle of
all repositories sharing a single session. This ensures atomic
operations across multiple repository calls.
"""

from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """
    Unit of Work context manager.
    
    Ensures that a series of database operations either commit
    successfully or roll back completely on error. Provides access
    to all repositories bound to the same session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        # Repositories are lazily instantiated to avoid overhead
        self._users = None
        self._groups = None
        self._members = None
        self._invite_links = None
        self._invite_records = None
        self._events = None
        self._admins = None
        
    async def __aenter__(self) -> Self:
        """Start the transaction context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the transaction context.
        Rolls back if an exception occurred, otherwise does nothing
        (caller must explicitly call commit() to save changes).
        """
        if exc_type is not None:
            await self.rollback()
        # Session closing is handled by the get_session dependency

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        await self.session.rollback()

    # ==================== Repository Accessors ====================
    # Lazy loading pattern avoids instantiating unused repositories

    @property
    def users(self):
        from bot.repositories.bot_user_repo import BotUserRepository
        if self._users is None:
            self._users = BotUserRepository(self.session)
        return self._users

    @property
    def groups(self):
        from bot.repositories.group_repo import GroupRepository
        if self._groups is None:
            self._groups = GroupRepository(self.session)
        return self._groups

    @property
    def members(self):
        from bot.repositories.member_repo import MemberRepository
        if self._members is None:
            self._members = MemberRepository(self.session)
        return self._members

    @property
    def invite_links(self):
        from bot.repositories.invite_link_repo import InviteLinkRepository
        if self._invite_links is None:
            self._invite_links = InviteLinkRepository(self.session)
        return self._invite_links

    @property
    def invite_records(self):
        from bot.repositories.invite_record_repo import InviteRecordRepository
        if self._invite_records is None:
            self._invite_records = InviteRecordRepository(self.session)
        return self._invite_records

    @property
    def events(self):
        from bot.repositories.member_event_repo import MemberEventRepository
        if self._events is None:
            self._events = MemberEventRepository(self.session)
        return self._events

    @property
    def admins(self):
        from bot.repositories.admin_repo import AdminRepository
        if self._admins is None:
            self._admins = AdminRepository(self.session)
        return self._admins
