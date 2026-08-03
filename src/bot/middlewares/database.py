"""
Database and Service Injection Middleware.

Intercepts every update to create a new SQLAlchemy AsyncSession.
It initializes the UnitOfWork and all business logic services,
injecting them into the handler's kwargs.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.repositories.unit_of_work import UnitOfWork
from bot.services.admin_service import AdminService
from bot.services.group_service import GroupService
from bot.services.invite_service import InviteTrackingService
from bot.services.notification_service import NotificationService


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware that creates a database session and services for each update.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Create session, init services, inject into data, and execute handler.
        """
        # Create a new database session for this specific update
        async with self.session_factory() as session:
            # Initialize Unit of Work
            uow = UnitOfWork(session)
            
            # Initialize Services with the UoW
            data["uow"] = uow
            data["group_service"] = GroupService(uow)
            data["invite_service"] = InviteTrackingService(uow)
            data["admin_service"] = AdminService(uow)
            data["notification_service"] = NotificationService(uow)

            # Note: We do NOT use 'async with uow' here because we don't 
            # want to automatically commit/rollback the entire update.
            # Services should handle their own transactions explicitly.
            
            # Pass execution to the handler
            return await handler(event, data)
