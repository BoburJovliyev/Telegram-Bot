"""
Throttling (Rate Limiting) Middleware.

Uses the central RateLimiter to implement rate limiting on commands and interactions
to protect the bot from spam and abuse.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from redis.asyncio import Redis

from bot.security.rate_limiter import RateLimiter


class ThrottlingMiddleware(BaseMiddleware):
    """
    Rate limiting middleware using the centralized RateLimiter.
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
        
        # We generally only care about throttling commands or private bot chats
        text = getattr(event, "text", "")
        if event.chat.type != "private" and (not text or not text.startswith("/")):
            return await handler(event, data)

        limiter = RateLimiter(redis)
        action = "global_msg"
        
        allowed = await limiter.check_rate_limit(user_id, action, self.rate_limit, self.timeout)

        if not allowed:
            # Drop the update
            return None

        return await handler(event, data)
