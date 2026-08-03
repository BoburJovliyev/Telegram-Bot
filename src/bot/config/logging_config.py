"""
Structlog configuration.

Sets up structured logging for the application. In production, logs
are output as JSON for easier ingestion into log aggregation tools.
In development, logs use a human-readable console renderer.
"""

import logging
import sys

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer

from bot.config import get_settings
from bot.logging.processors import extract_telegram_context, mask_secrets


def configure_logging() -> None:
    """
    Configure structured logging based on application settings.
    
    Initializes the standard library logging module and wires it up
    to structlog with appropriate formatters and processors.
    """
    settings = get_settings()
    log_level_name = settings.log_level.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Base processors applied to all log events
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        extract_telegram_context,
        mask_secrets,
    ]

    # Output formatting depends on the environment
    if settings.log_json:
        # JSON format for production (e.g. for ELK/Datadog)
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                *shared_processors,
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                JSONRenderer(),
            ],
        )
    else:
        # Human-readable format for development
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                *shared_processors,
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                ConsoleRenderer(colors=True),
            ],
        )

    # Configure the root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Configure structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set levels for noisy libraries
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)

    # Database echo configures SQLAlchemy's internal logger
    if settings.database_echo:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
