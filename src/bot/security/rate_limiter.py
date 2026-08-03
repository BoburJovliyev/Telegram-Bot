"""
Redis-backed Rate Limiter using a Fixed Window algorithm.
"""

import time
from redis.asyncio import Redis


class RateLimiter:
    """
    Limits the number of actions a user can perform within a specific time window.
    """

    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_rate_limit(self, user_id: int, action: str, limit: int, window_seconds: int) -> bool:
        """
        Check if the user has exceeded the rate limit for a specific action.
        Uses a simple fixed window counter in Redis.
        
        Args:
            user_id: The Telegram user ID.
            action: The action being rate limited (e.g., 'command_stats').
            limit: Maximum allowed requests in the window.
            window_seconds: The time window in seconds.
            
        Returns:
            True if the request is allowed, False if rate limited.
        """
        # Current window based on epoch time
        current_window = int(time.time() / window_seconds)
        key = f"rate_limit:{user_id}:{action}:{current_window}"
        
        # Increment counter and set expiry if it's new
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, window_seconds + 1)
            results = await pipe.execute()
            
        count = results[0]
        
        return count <= limit
