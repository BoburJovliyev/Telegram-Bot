"""
Contextual Logging Middleware.

Binds the Telegram user ID and chat ID to the structlog contextvars
so that every log message generated during the update contains
this attribution automatically.
"""

from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, ChatMemberUpdated


class LoggingMiddleware(BaseMiddleware):
    """
    Binds update context to structlog contextvars.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Extract IDs from the event and bind them to the logger context."""
        
        # Clear context variables from previous updates (important for asyncio)
        structlog.contextvars.clear_contextvars()
        
        context_kwargs = {}
        
        # Extract Chat ID
        if getattr(event, "chat", None):
            context_kwargs["chat_id"] = event.chat.id
            
        # Extract User ID based on event type
        if isinstance(event, Message) and event.from_user:
            context_kwargs["user_id"] = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            context_kwargs["user_id"] = event.from_user.id
        elif isinstance(event, ChatMemberUpdated) and event.from_user:
            context_kwargs["user_id"] = event.from_user.id

        # Bind variables if found
        if context_kwargs:
            structlog.contextvars.bind_contextvars(**context_kwargs)
            
        return await handler(event, data)
