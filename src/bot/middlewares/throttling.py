"""
Throttling (Rate Limiting) Middleware.

Uses Redis to implement rate limiting on commands and interactions
to protect the bot from spam and abuse.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from redis.asyncio import Redis


class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple rate limiting middleware using Redis.
    Limits users to X messages per Y seconds.
    """

    def __init__(self, rate_limit: int = 1, timeout: int = 2) -> None:
        """
        Args:
            rate_limit: Number of allowed requests.
            timeout: Time window in seconds.
        """
        self.rate_limit = rate_limit
        self.timeout = timeout

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Apply rate limiting logic."""
        # We only throttle messages for now
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        redis: Redis = data.get("redis")
        if not redis:
            # If Redis isn't configured, bypass throttling
            return await handler(event, data)

        user_id = event.from_user.id
        # Differentiate between group messages and private messages
        chat_id = event.chat.id
        
        # We generally only care about throttling commands or private bot chats
        # Throttling every message in a busy group will overwhelm Redis unnecessarily.
        # Only throttle if it's a private chat or a command in a group.
        if event.chat.type != "private" and not event.text?.startswith("/"):
            return await handler(event, data)

        key = f"throttle:{chat_id}:{user_id}"
        
        # Atomic Redis operation: increment counter and set expiry if it's new
        async with redis.pipeline() as pipe:
            pipe.incr(key)
            pipe.expire(key, self.timeout, nx=True)
            results = await pipe.execute()
            
        current_count = results[0]

        if current_count > self.rate_limit:
            # Drop the update
            return None

        return await handler(event, data)
