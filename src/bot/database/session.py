"""
Database session dependency.

Provides a context manager and dependency injection pattern
for obtaining AsyncSession instances scoped to a single
unit of work (typically one Telegram update processing cycle).

The session is injected by the DatabaseMiddleware and passed
through the handler chain via Aiogram's data dict.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator that yields a database session.

    Creates a new session, yields it for use, and ensures
    proper cleanup (close) regardless of success or failure.

    This function is designed to be used by the DatabaseMiddleware
    to inject a session into each handler's data context.

    Args:
        session_factory: The async_sessionmaker to create sessions from.

    Yields:
        An AsyncSession instance for database operations.

    Notes:
        - The caller is responsible for committing the session.
        - If an exception occurs, the session is rolled back
          and closed automatically.
        - Multiple handlers processing different updates get
          independent sessions (no cross-request contamination).
    """
    session = session_factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
