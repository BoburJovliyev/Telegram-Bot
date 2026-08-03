"""
Application settings using Pydantic BaseSettings.

All configuration is loaded from environment variables with
sensible defaults. Settings are validated at startup — if
any required value is missing, the application fails fast
with a clear error message.

Environment variables can be provided via:
1. .env file (auto-loaded by Pydantic)
2. System environment variables
3. Docker secrets
4. docker-compose environment section
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root directory (3 levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """
    Application configuration.

    All fields with defaults can be overridden via environment variables.
    Fields without defaults are REQUIRED and the app will not start without them.
    """

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== Bot Configuration ====================
    bot_token: str = Field(
        default="8887391932:AAHSmJjxk9jlMJHTBwbRGRtZgrI92rLs-jU",
        description="Telegram Bot API token from @BotFather.",
        alias="BOT_TOKEN",
    )

    bot_owner_id: int = Field(
        default=8254782802,
        description="Telegram user ID of the bot owner (superadmin).",
        alias="BOT_OWNER_ID",
    )

    super_admin_ids: list[int] = Field(
        default_factory=list,
        description="List of Telegram user IDs with super admin privileges.",
        alias="SUPER_ADMIN_IDS",
    )

    # ==================== Polling / Webhook ====================
    use_webhook: bool = Field(
        default=False,
        description="Use webhook mode instead of long polling.",
        alias="USE_WEBHOOK",
    )

    webhook_url: str = Field(
        default="",
        description="Public URL for webhook (required if use_webhook=True).",
        alias="WEBHOOK_URL",
    )

    webhook_secret: str = Field(
        default="",
        description="Secret token for webhook verification.",
        alias="WEBHOOK_SECRET",
    )

    webhook_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the webhook server to.",
        alias="WEBHOOK_HOST",
    )

    webhook_port: int = Field(
        default=8443,
        description="Port for the webhook server.",
        alias="WEBHOOK_PORT",
    )

    # ==================== Database ====================
    database_url: str = Field(
        default="sqlite+aiosqlite:///invite_tracker.db",
        description="SQLite connection URL.",
        alias="DATABASE_URL",
    )

    database_echo: bool = Field(
        default=False,
        description="Log all SQL queries (development only).",
        alias="DATABASE_ECHO",
    )



    # ==================== Logging ====================
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
        alias="LOG_LEVEL",
    )

    log_dir: str = Field(
        default=str(BASE_DIR / "logs"),
        description="Directory for log files.",
        alias="LOG_DIR",
    )

    log_json: bool = Field(
        default=True,
        description="Use JSON format for log output.",
        alias="LOG_JSON",
    )

    # ==================== Environment ====================
    environment: str = Field(
        default="development",
        description="Environment name (development, staging, production).",
        alias="ENVIRONMENT",
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode.",
        alias="DEBUG",
    )

    # ==================== Monitoring ====================
    enable_metrics: bool = Field(
        default=True,
        description="Enable Prometheus metrics endpoint.",
        alias="ENABLE_METRICS",
    )

    metrics_port: int = Field(
        default=9090,
        description="Port for Prometheus metrics endpoint.",
        alias="METRICS_PORT",
    )

    health_check_port: int = Field(
        default=8080,
        description="Port for health check endpoint.",
        alias="HEALTH_CHECK_PORT",
    )

    # ==================== Timezone ====================
    default_timezone: str = Field(
        default="UTC",
        description="Default timezone for reports (IANA format).",
        alias="DEFAULT_TIMEZONE",
    )

    # ==================== Validators ====================
    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate that the bot token follows Telegram's format."""
        if not v or ":" not in v:
            raise ValueError(
                "Invalid bot token format. "
                "Expected format: '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'"
            )
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure the database URL uses the aiosqlite driver."""
        if not v.startswith("sqlite+aiosqlite://"):
            raise ValueError(
                "Database URL must use the aiosqlite driver. "
                "Expected format: 'sqlite+aiosqlite:///db.sqlite3'"
            )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a recognized Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(
                f"Invalid log level '{v}'. Must be one of: {valid_levels}"
            )
        return upper

    @field_validator("super_admin_ids", mode="before")
    @classmethod
    def parse_super_admin_ids(cls, v: str | list[int]) -> list[int]:
        """Parse comma-separated string of IDs into a list of integers."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached application settings singleton.

    Settings are loaded once from environment variables and cached
    for the lifetime of the process. Subsequent calls return the
    same instance.

    Returns:
        The application Settings instance.
    """
    return Settings()
