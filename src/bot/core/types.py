"""
Custom type aliases for the Telegram Invite Tracker Bot.

Centralizes all custom type definitions to improve readability,
enforce consistency, and enable easy refactoring across the codebase.
"""

from typing import TypeAlias
from uuid import UUID

# ==============================================================================
# Telegram ID Types
# ==============================================================================
# Telegram user IDs are positive 64-bit integers.
# Telegram chat IDs for supergroups are negative 64-bit integers.
# Using explicit type aliases makes function signatures self-documenting.

TelegramUserId: TypeAlias = int
"""Telegram user ID — always a positive integer."""

TelegramChatId: TypeAlias = int
"""Telegram chat/group ID — negative for supergroups, positive for private chats."""

TelegramMessageId: TypeAlias = int
"""Telegram message ID — positive integer, unique within a chat."""

# ==============================================================================
# Database ID Types
# ==============================================================================

PrimaryKey: TypeAlias = UUID
"""UUID v4 primary key used for internal database records."""

# ==============================================================================
# Invite Link Types
# ==============================================================================

InviteLinkUrl: TypeAlias = str
"""Full Telegram invite link URL (e.g., 'https://t.me/+AbCdEfGhIjK')."""

InviteLinkName: TypeAlias = str
"""Human-readable label for an invite link (max 32 chars per Telegram API)."""

# ==============================================================================
# Statistics Types
# ==============================================================================

CounterValue: TypeAlias = int
"""Non-negative integer counter (e.g., total_invited, active_invited)."""

# ==============================================================================
# Generic Types
# ==============================================================================

JsonDict: TypeAlias = dict[str, object]
"""A JSON-serializable dictionary used for metadata and settings storage."""
