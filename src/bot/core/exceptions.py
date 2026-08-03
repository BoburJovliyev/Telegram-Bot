"""
Custom exception hierarchy for the Telegram Invite Tracker Bot.

All application-specific exceptions are defined here following a
hierarchical structure. Each layer of the application raises
domain-specific exceptions, which are caught and handled by
the error-handling middleware.

Exception Hierarchy:
    BotError (base)
    ├── ConfigurationError
    ├── DatabaseError
    │   ├── RecordNotFoundError
    │   ├── DuplicateRecordError
    │   └── TransactionError
    ├── TelegramAPIError
    ├── PermissionError
    │   ├── InsufficientRoleError
    │   └── GroupNotRegisteredError
    ├── RateLimitError
    ├── ValidationError
    ├── InviteTrackingError
    │   ├── DuplicateInviteError
    │   └── InvalidInviteLinkError
    ├── ExportError
    └── NotificationError
"""

from bot.core.enums import UserRole
from bot.core.types import PrimaryKey, TelegramChatId, TelegramUserId


class BotError(Exception):
    """
    Base exception for all application errors.

    All custom exceptions inherit from this class so that
    the global error handler can distinguish between expected
    application errors and unexpected system errors.
    """

    def __init__(self, message: str = "An unexpected error occurred") -> None:
        self.message = message
        super().__init__(self.message)


# ==============================================================================
# Configuration Errors
# ==============================================================================


class ConfigurationError(BotError):
    """Raised when application configuration is invalid or missing."""

    def __init__(self, message: str = "Invalid configuration") -> None:
        super().__init__(f"Configuration error: {message}")


# ==============================================================================
# Database Errors
# ==============================================================================


class DatabaseError(BotError):
    """Base exception for all database-related errors."""

    def __init__(self, message: str = "Database operation failed") -> None:
        super().__init__(f"Database error: {message}")


class RecordNotFoundError(DatabaseError):
    """Raised when a requested database record does not exist."""

    def __init__(
        self,
        model_name: str,
        identifier: PrimaryKey | TelegramUserId | TelegramChatId | str,
    ) -> None:
        self.model_name = model_name
        self.identifier = identifier
        super().__init__(f"{model_name} with ID '{identifier}' not found")


class DuplicateRecordError(DatabaseError):
    """Raised when attempting to insert a record that already exists."""

    def __init__(self, model_name: str, details: str = "") -> None:
        self.model_name = model_name
        extra = f": {details}" if details else ""
        super().__init__(f"Duplicate {model_name} record{extra}")


class TransactionError(DatabaseError):
    """Raised when a database transaction fails to commit or rollback."""

    def __init__(self, message: str = "Transaction failed") -> None:
        super().__init__(message)


# ==============================================================================
# Telegram API Errors
# ==============================================================================


class TelegramAPIError(BotError):
    """
    Raised when a Telegram Bot API call fails unexpectedly.

    Wraps Aiogram's TelegramAPIError with additional context.
    """

    def __init__(
        self,
        method: str,
        message: str = "Telegram API call failed",
    ) -> None:
        self.method = method
        super().__init__(f"Telegram API error in {method}: {message}")


# ==============================================================================
# Permission Errors
# ==============================================================================


class PermissionDeniedError(BotError):
    """Base exception for permission-related failures."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(f"Permission denied: {message}")


class InsufficientRoleError(PermissionDeniedError):
    """Raised when a user's role does not meet the required level."""

    def __init__(
        self,
        user_id: TelegramUserId,
        required_role: UserRole,
        actual_role: UserRole,
    ) -> None:
        self.user_id = user_id
        self.required_role = required_role
        self.actual_role = actual_role
        super().__init__(
            f"User {user_id} has role '{actual_role.value}' "
            f"but '{required_role.value}' is required"
        )


class GroupNotRegisteredError(PermissionDeniedError):
    """Raised when an operation is attempted on an unregistered group."""

    def __init__(self, chat_id: TelegramChatId) -> None:
        self.chat_id = chat_id
        super().__init__(f"Group {chat_id} is not registered with the bot")


# ==============================================================================
# Rate Limiting Errors
# ==============================================================================


class RateLimitError(BotError):
    """Raised when a user exceeds their rate limit."""

    def __init__(
        self,
        user_id: TelegramUserId,
        retry_after: int,
    ) -> None:
        self.user_id = user_id
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for user {user_id}. "
            f"Retry after {retry_after} seconds."
        )


# ==============================================================================
# Validation Errors
# ==============================================================================


class InputValidationError(BotError):
    """Raised when user input fails validation checks."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        super().__init__(f"Validation error for '{field}': {message}")


# ==============================================================================
# Invite Tracking Errors
# ==============================================================================


class InviteTrackingError(BotError):
    """Base exception for invite tracking failures."""

    def __init__(self, message: str = "Invite tracking error") -> None:
        super().__init__(f"Invite tracking: {message}")


class DuplicateInviteError(InviteTrackingError):
    """
    Raised when a duplicate invite record is detected.

    This can happen due to race conditions or repeated events.
    The system handles this gracefully by ignoring the duplicate.
    """

    def __init__(
        self,
        inviter_id: TelegramUserId | None,
        invitee_id: TelegramUserId,
        group_id: TelegramChatId,
    ) -> None:
        self.inviter_id = inviter_id
        self.invitee_id = invitee_id
        self.group_id = group_id
        super().__init__(
            f"Duplicate invite: user {invitee_id} already tracked "
            f"in group {group_id}"
        )


class InvalidInviteLinkError(InviteTrackingError):
    """Raised when an invite link cannot be validated or processed."""

    def __init__(self, link: str, reason: str) -> None:
        self.link = link
        self.reason = reason
        super().__init__(f"Invalid invite link '{link}': {reason}")


# ==============================================================================
# Export Errors
# ==============================================================================


class ExportError(BotError):
    """Raised when report export generation fails."""

    def __init__(self, format_name: str, message: str) -> None:
        self.format_name = format_name
        super().__init__(f"Export error ({format_name}): {message}")


# ==============================================================================
# Notification Errors
# ==============================================================================


class NotificationError(BotError):
    """Raised when a notification fails to send."""

    def __init__(
        self,
        recipient_id: TelegramUserId | TelegramChatId,
        message: str = "Failed to send notification",
    ) -> None:
        self.recipient_id = recipient_id
        super().__init__(f"Notification to {recipient_id} failed: {message}")
