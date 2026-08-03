"""
Access Control List (ACL) Middleware.

Injects the user's role into the handler context data.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from bot.security.permissions import PermissionsEngine


class ACLMiddleware(BaseMiddleware):
    """
    Middleware to determine and inject the user's role.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        
        # We need a user and a chat context
        user = data.get("event_from_user")
        chat = data.get("event_chat")
        
        if not user or not chat:
            return await handler(event, data)

        session_factory: async_sessionmaker[AsyncSession] = data.get("session_factory")
        if not session_factory:
            return await handler(event, data)

        async with session_factory() as session:
            permissions = PermissionsEngine(session)
            role = await permissions.get_user_role(chat.id, user.id)

        # Inject role into context data
        data["user_role"] = role

        return await handler(event, data)
