"""
Time utility functions.
"""
from datetime import datetime, date, timezone
from bot.config import get_settings
import zoneinfo

def get_current_datetime() -> datetime:
    """Get the current timezone-aware datetime based on the configured default timezone."""
    settings = get_settings()
    try:
        tz = zoneinfo.ZoneInfo(settings.default_timezone)
    except Exception:
        tz = timezone.utc
    
    return datetime.now(tz)

def get_current_date() -> date:
    """Get the current date based on the configured default timezone."""
    return get_current_datetime().date()
