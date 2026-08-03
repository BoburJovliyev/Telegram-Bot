"""
Application Factory.

Responsible for assembling all the disparate parts of the application
into a running bot instance. This includes setting up the bot,
dispatcher, database engine, redis pool, and scheduler.
"""

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from bot.config import get_settings
from bot.database.engine import create_engine, create_session_factory
from bot.models.base import Base
# Handlers and middlewares will be imported and registered here later

logger = structlog.get_logger(__name__)


class Application:
    """
    Main application container.
    Holds references to all core services and dependencies.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self.scheduler: AsyncIOScheduler | None = None

    async def initialize(self) -> None:
        """Initialize all application components."""
        logger.info("Initializing application components...")
        
        # 1. Database
        self.engine = create_engine(
            database_url=self.settings.database_url,
            echo=self.settings.database_echo,
        )
        self.session_factory = create_session_factory(self.engine)
        
        # Auto-create tables for SQLite
        import bot.models  # Ensure all models are registered
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database engine initialized and tables created")



        # 3. Scheduler
        self.scheduler = AsyncIOScheduler()
        self.setup_jobs()
        self.scheduler.start()
        logger.info("APScheduler started")

        # 4. Bot & Dispatcher
        self.bot = Bot(
            token=self.settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # We use MemoryStorage for FSM
        storage = MemoryStorage()
        
        self.dp = Dispatcher(storage=storage)
        
        # Dependency injection via WorkflowData
        self.dp["session_factory"] = self.session_factory
        self.dp["scheduler"] = self.scheduler
        self.dp["settings"] = self.settings

        # Middlewares and Routers will be registered here later
        self.setup_middlewares()
        self.setup_routers()
        
        logger.info("Bot and Dispatcher initialized")

    async def dispose(self) -> None:
        """Gracefully shut down all application components."""
        logger.info("Shutting down application...")
        
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")
            
        if self.bot:
            await self.bot.session.close()
            logger.info("Bot session closed")
            

            
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine disposed")
            
        logger.info("Shutdown complete")

    def setup_middlewares(self) -> None:
        """Register all middlewares on the dispatcher."""
        from bot.middlewares.database import DatabaseMiddleware
        from bot.middlewares.logging import LoggingMiddleware
        from bot.middlewares.throttling import ThrottlingMiddleware
        from bot.middlewares.acl import ACLMiddleware
        
        logger.info("Registering middlewares...")
        
        # Logging goes first so context is bound immediately
        self.dp.update.outer_middleware(LoggingMiddleware())
        
        # Database goes before ACL so the ACL middleware has access to the session_factory
        self.dp.update.outer_middleware(DatabaseMiddleware(self.session_factory))
        
        # ACL middleware attaches user_role to the context
        self.dp.update.outer_middleware(ACLMiddleware())
        
        # Throttling goes next to drop spam early
        self.dp.message.middleware(ThrottlingMiddleware(rate_limit=1, timeout=2))

    def setup_routers(self) -> None:
        """Register the root router."""
        from bot.routers import setup_routers
        
        logger.info("Registering routers...")
        root_router = setup_routers()
        self.dp.include_router(root_router)

    def setup_jobs(self) -> None:
        """Register all APScheduler background jobs."""
        from bot.scheduler.setup import setup_scheduler
        
        if self.scheduler and self.session_factory and self.bot:
            setup_scheduler(self.scheduler, self.session_factory, self.bot)
