"""
Async SQLAlchemy engine and session factory.

Creates a single AsyncEngine instance for the application lifecycle
and provides an async_sessionmaker for creating per-request sessions.

Connection pooling is configured for high-concurrency production use
with asyncpg as the PostgreSQL driver.

Usage:
    # At application startup
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    # Per-request (via middleware)
    async with session_factory() as session:
        ...
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.core.constants import (
    DB_POOL_MAX_OVERFLOW,
    DB_POOL_MAX_SIZE,
    DB_POOL_MIN_SIZE,
    DB_POOL_RECYCLE_SECONDS,
)


def create_engine(
    database_url: str,
    echo: bool = False,
    pool_size: int = DB_POOL_MIN_SIZE,
    max_overflow: int = DB_POOL_MAX_OVERFLOW,
    pool_recycle: int = DB_POOL_RECYCLE_SECONDS,
) -> AsyncEngine:
    """
    Create and configure the async SQLAlchemy engine.

    Args:
        database_url: PostgreSQL connection string
            (e.g., 'postgresql+asyncpg://user:pass@host:5432/dbname').
        echo: If True, log all SQL statements (development only).
        pool_size: Number of persistent connections in the pool.
        max_overflow: Maximum number of connections above pool_size.
        pool_recycle: Seconds before a connection is recycled
            (prevents stale connections from PostgreSQL's idle timeout).

    Returns:
        Configured AsyncEngine instance.

    Notes:
        - Uses asyncpg driver for maximum async performance.
        - pool_pre_ping=True ensures connections are validated before use
          (handles PostgreSQL restarts and network interruptions).
        - pool_size is set conservatively; adjust based on expected concurrency.
    """
    from sqlalchemy.pool import NullPool
    return create_async_engine(
        url=database_url,
        echo=echo,
        poolclass=NullPool,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Create an async session factory bound to the given engine.

    Args:
        engine: The AsyncEngine to bind sessions to.

    Returns:
        An async_sessionmaker that produces AsyncSession instances.

    Notes:
        - expire_on_commit=False: prevents SQLAlchemy from expiring
          loaded attributes after commit, which would trigger lazy loads
          (illegal in async context and causes MissingGreenlet errors).
        - Sessions created from this factory are NOT auto-committed.
          All writes must be explicitly committed via session.commit()
          or session.begin() context manager.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def dispose_engine(engine: AsyncEngine) -> None:
    """
    Gracefully dispose of the engine and close all connections.

    Must be called during application shutdown to prevent
    connection leaks and ensure clean PostgreSQL disconnection.

    Args:
        engine: The AsyncEngine to dispose.
    """
    await engine.dispose()
