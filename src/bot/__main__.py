"""
Main entry point for the Telegram Invite Tracker Bot.

Configures logging, creates the application instance, and starts
the bot (either via polling or webhook based on configuration).
"""

import asyncio
import sys

import structlog

from bot.app import Application
from bot.config import get_settings
from bot.config.logging_config import configure_logging

logger = structlog.get_logger(__name__)


async def main() -> None:
    """Run the application lifecycle."""
    # 1. Setup logging first
    configure_logging()
    settings = get_settings()
    
    logger.info(
        "Starting Telegram Invite Tracker Bot",
        version="1.0.0",
        environment=settings.environment,
        mode="webhook" if settings.use_webhook else "polling"
    )

    # 2. Create and initialize application
    app = Application()
    
    try:
        await app.initialize()
        
        # 3. Start bot
        if not app.bot or not app.dp:
            raise RuntimeError("Bot or Dispatcher not initialized")
            
        if settings.use_webhook:
            logger.info("Starting webhook server...")
            # Webhook setup will go here (requires aiohttp/fastapi)
            # For now, just a placeholder
            raise NotImplementedError("Webhook mode not fully implemented yet")
        else:
            logger.info("Starting long polling...")
            # Drop pending updates to avoid processing old events
            await app.bot.delete_webhook(drop_pending_updates=True)
            # allowed_updates is critical for chat_member events
            await app.dp.start_polling(
                app.bot,
                allowed_updates=[
                    "message", 
                    "callback_query", 
                    "chat_member", 
                    "chat_join_request",
                    "my_chat_member"
                ]
            )
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.exception("Fatal error during bot execution", error=str(e))
        sys.exit(1)
    finally:
        await app.dispose()


if __name__ == "__main__":
    # Ensure Windows compatibility for asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
