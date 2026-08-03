"""
In-Memory Rate Limiter using a Fixed Window algorithm.
"""

import time
from collections import defaultdict


class RateLimiter:
    """
    Limits the number of actions a user can perform within a specific time window.
    """

    _store: dict[str, int] = defaultdict(int)
    _last_cleanup: float = time.time()

    def __init__(self):
        pass

    async def check_rate_limit(self, user_id: int, action: str, limit: int, window_seconds: int) -> bool:
        """
        Check if the user has exceeded the rate limit for a specific action.
        Uses a simple fixed window counter in memory.
        """
        now = time.time()
        
        # Simple cleanup to prevent memory leak (cleanup every 5 minutes)
        if now - self._last_cleanup > 300:
            self._store.clear()
            self.__class__._last_cleanup = now

        current_window = int(now / window_seconds)
        key = f"rate_limit:{user_id}:{action}:{current_window}"
        
        self._store[key] += 1
        count = self._store[key]
        
        return count <= limit
