"""
Custom structlog processors for contextual logging.

These processors extract contextual information (such as Telegram
user IDs, group IDs, or trace IDs) and inject them into the log
event dictionary before formatting.
"""

from typing import Any

from structlog.types import EventDict


def extract_telegram_context(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Extracts Telegram-specific context if available and adds it to the log event.
    
    If 'user_id' or 'chat_id' are bound to the logger context (typically via
    middleware), this processor ensures they are cleanly formatted in the output.
    """
    # This is a placeholder for more advanced context extraction.
    # structlog's bound variables are typically already included in the event_dict,
    # but this processor can be used to rename or format them explicitly.
    
    if "user_id" in event_dict:
        event_dict["telegram_user_id"] = event_dict.pop("user_id")
        
    if "chat_id" in event_dict:
        event_dict["telegram_chat_id"] = event_dict.pop("chat_id")
        
    return event_dict


def mask_secrets(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Masks sensitive information in log events.
    """
    sensitive_keys = {"token", "secret", "password", "key"}
    
    for key, value in event_dict.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_dict[key] = "***MASKED***"
            
    return event_dict
