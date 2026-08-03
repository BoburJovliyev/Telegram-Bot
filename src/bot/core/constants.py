"""
Application-wide constants for the Telegram Invite Tracker Bot.

All magic numbers, default values, limits, and configuration constants
are defined here. No hardcoded values should exist in business logic.
"""

# ==============================================================================
# Application Metadata
# ==============================================================================

APP_NAME: str = "Telegram Invite Tracker Bot"
APP_VERSION: str = "1.0.0"
APP_DESCRIPTION: str = (
    "Enterprise-grade Telegram bot for tracking group invitations "
    "and counting which member invited which new users."
)

# ==============================================================================
# Telegram Bot API Constants
# ==============================================================================

# Maximum length for invite link names (Telegram API restriction)
MAX_INVITE_LINK_NAME_LENGTH: int = 32

# Maximum message length for Telegram messages
MAX_MESSAGE_LENGTH: int = 4096

# Maximum caption length for Telegram media
MAX_CAPTION_LENGTH: int = 1024

# Maximum number of inline keyboard buttons per row
MAX_INLINE_BUTTONS_PER_ROW: int = 8

# Maximum number of rows in an inline keyboard
MAX_INLINE_KEYBOARD_ROWS: int = 100

# Maximum file size for document uploads (50 MB)
MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024

# ==============================================================================
# Rate Limiting
# ==============================================================================

# Default rate limit: requests per minute per user
DEFAULT_USER_RATE_LIMIT: int = 30

# Rate limit for commands per minute per group
DEFAULT_GROUP_RATE_LIMIT: int = 60

# Rate limit for expensive operations (export, report) per minute per user
HEAVY_COMMAND_RATE_LIMIT: int = 5

# Sliding window size for rate limiting (in seconds)
RATE_LIMIT_WINDOW_SECONDS: int = 60

# ==============================================================================
# Caching TTLs (in seconds)
# ==============================================================================

CACHE_TTL_LEADERBOARD: int = 300  # 5 minutes
CACHE_TTL_MEMBER_STATS: int = 120  # 2 minutes
CACHE_TTL_GROUP_INFO: int = 600  # 10 minutes
CACHE_TTL_ADMIN_LIST: int = 300  # 5 minutes
CACHE_TTL_DAILY_STATS: int = 86400  # 24 hours

# ==============================================================================
# Pagination
# ==============================================================================

# Default number of items per page in paginated lists
DEFAULT_PAGE_SIZE: int = 10

# Maximum number of items per page
MAX_PAGE_SIZE: int = 50

# Number of top inviters to show in leaderboard
DEFAULT_LEADERBOARD_SIZE: int = 10

# ==============================================================================
# Database
# ==============================================================================

# Minimum PostgreSQL connection pool size
DB_POOL_MIN_SIZE: int = 5

# Maximum PostgreSQL connection pool size
DB_POOL_MAX_SIZE: int = 20

# Connection pool overflow allowance
DB_POOL_MAX_OVERFLOW: int = 10

# Connection pool recycle time (in seconds) to prevent stale connections
DB_POOL_RECYCLE_SECONDS: int = 3600

# Query timeout (in seconds)
DB_QUERY_TIMEOUT_SECONDS: int = 30

# ==============================================================================
# Scheduled Jobs
# ==============================================================================

# Daily report generation time (UTC)
DAILY_REPORT_HOUR: int = 0
DAILY_REPORT_MINUTE: int = 5

# Weekly report generation — day of week (0=Monday, 6=Sunday)
WEEKLY_REPORT_DAY: int = 0  # Monday
WEEKLY_REPORT_HOUR: int = 0
WEEKLY_REPORT_MINUTE: int = 30

# Monthly report generation — day of month
MONTHLY_REPORT_DAY: int = 1
MONTHLY_REPORT_HOUR: int = 1
MONTHLY_REPORT_MINUTE: int = 0

# Database cleanup interval (in hours)
CLEANUP_INTERVAL_HOURS: int = 24

# Stats aggregation interval (in minutes)
STATS_AGGREGATION_INTERVAL_MINUTES: int = 30

# Health check interval (in minutes)
HEALTH_CHECK_INTERVAL_MINUTES: int = 5

# ==============================================================================
# Notifications
# ==============================================================================

# Invite milestone thresholds that trigger notifications
INVITE_MILESTONES: list[int] = [10, 25, 50, 100, 250, 500, 1000, 5000, 10000]

# Maximum notifications per group per hour (flood protection)
MAX_NOTIFICATIONS_PER_HOUR: int = 50

# ==============================================================================
# Security
# ==============================================================================

# Maximum failed permission checks before temporary lockout
MAX_PERMISSION_FAILURES: int = 10

# Lockout duration after exceeding failed permission checks (in seconds)
PERMISSION_LOCKOUT_SECONDS: int = 300  # 5 minutes

# Maximum concurrent join events to process (anti-spam)
MAX_CONCURRENT_JOINS_PER_MINUTE: int = 100

# Threshold for detecting suspicious join patterns
SUSPICIOUS_JOIN_THRESHOLD: int = 50  # 50 joins in 1 minute

# ==============================================================================
# Exports
# ==============================================================================

# Maximum rows in a single export file
MAX_EXPORT_ROWS: int = 100_000

# Export file retention period (in days)
EXPORT_RETENTION_DAYS: int = 7

# ==============================================================================
# Monitoring
# ==============================================================================

# Prometheus metrics endpoint port
METRICS_PORT: int = 9090

# Health check endpoint port
HEALTH_CHECK_PORT: int = 8080
