"""
Pytest configuration and async fixtures.

Sets up the testing environment, in-memory SQLite (or test Postgres),
and mocks the Telegram Bot API so handlers can be unit tested without
network calls.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from bot.database.base import Base
from bot.repositories.unit_of_work import UnitOfWork

# Use an in-memory SQLite database for fast unit testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a database engine and all tables for tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture()
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional database session for a single test.
    Rolls back automatically after the test finishes to ensure isolation.
    """
    connection = await engine.connect()
    transaction = await connection.begin()
    
    session_factory = sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    session = session_factory()
    yield session
    
    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest.fixture()
def uow(db_session: AsyncSession) -> UnitOfWork:
    """Provide a UnitOfWork bound to the isolated test session."""
    return UnitOfWork(db_session)

@pytest.fixture()
def mock_bot() -> AsyncMock:
    """Provide a mocked Telegram Bot."""
    bot = AsyncMock(spec=Bot)
    bot.id = 123456789
    return bot
