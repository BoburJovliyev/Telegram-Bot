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
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from bot.config import get_settings
from bot.database.engine import create_engine, create_session_factory
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
        self.redis: Redis | None = None
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
        logger.info("Database engine initialized")

        # 2. Redis
        self.redis = Redis.from_url(
            self.settings.redis_url, 
            decode_responses=True
        )
        # Test connection
        await self.redis.ping()
        logger.info("Redis connected")

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
        
        # We use RedisStorage for FSM
        storage = RedisStorage(redis=self.redis)
        
        self.dp = Dispatcher(storage=storage)
        
        # Dependency injection via WorkflowData
        self.dp["session_factory"] = self.session_factory
        self.dp["redis"] = self.redis
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
            
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
            
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine disposed")
            
        logger.info("Shutdown complete")

    def setup_middlewares(self) -> None:
        """Register all middlewares on the dispatcher."""
        from bot.middlewares.database import DatabaseMiddleware
        from bot.middlewares.logging import LoggingMiddleware
        from bot.middlewares.throttling import ThrottlingMiddleware
        
        logger.info("Registering middlewares...")
        
        # Logging goes first so context is bound immediately
        self.dp.update.outer_middleware(LoggingMiddleware())
        
        # Throttling goes next to drop spam early
        self.dp.message.middleware(ThrottlingMiddleware(rate_limit=1, timeout=2))
        
        # Database goes last to avoid opening DB sessions for dropped spam
        self.dp.update.outer_middleware(DatabaseMiddleware(self.session_factory))

    def setup_routers(self) -> None:
        """Register the root router."""
        from bot.routers import setup_routers
        
        logger.info("Registering routers...")
        root_router = setup_routers()
        self.dp.include_router(root_router)

    def setup_jobs(self) -> None:
        """Register all APScheduler background jobs."""
        from bot.jobs.stats_aggregator import aggregate_daily_stats
        
        logger.info("Registering scheduled jobs...")
        
        # Run daily stats aggregation every 30 minutes
        self.scheduler.add_job(
            aggregate_daily_stats,
            trigger="interval",
            minutes=30,
            kwargs={"session_factory": self.session_factory},
            id="aggregate_daily_stats",
            replace_existing=True,
        )
