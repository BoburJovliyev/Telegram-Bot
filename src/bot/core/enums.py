"""
Core enumerations for the Telegram Invite Tracker Bot.

All domain-specific enumerations are defined here and used across
models, services, handlers, and repositories to ensure type safety
and consistency throughout the application.
"""

from enum import StrEnum, unique


@unique
class JoinMethod(StrEnum):
    """
    How a user joined a Telegram group.

    Determined by analyzing the ChatMemberUpdated event:
    - INVITE_LINK: joined via a tracked private invite link
    - ADDED_BY_ADMIN: added directly by an admin/user (from_user != new_member)
    - JOIN_REQUEST: joined after a join request was approved
    - PUBLIC: joined via public group username or search
    - UNKNOWN: unable to determine (edge cases, bot was offline)
    """

    INVITE_LINK = "invite_link"
    ADDED_BY_ADMIN = "added_by_admin"
    JOIN_REQUEST = "join_request"
    PUBLIC = "public"
    UNKNOWN = "unknown"


@unique
class MemberStatus(StrEnum):
    """
    Current status of a member within a group.

    Maps to Telegram's ChatMember status types:
    - ACTIVE: currently a member of the group
    - LEFT: voluntarily left the group
    - KICKED: removed by an admin (may or may not be banned)
    - BANNED: banned from the group (cannot rejoin)
    - RESTRICTED: member with restricted permissions
    """

    ACTIVE = "active"
    LEFT = "left"
    KICKED = "kicked"
    BANNED = "banned"
    RESTRICTED = "restricted"


@unique
class AdminRole(StrEnum):
    """
    Role of an administrator within a group.

    - OWNER: the group creator (Telegram: 'creator')
    - ADMIN: a promoted administrator (Telegram: 'administrator')
    - MODERATOR: a custom role with limited permissions (app-level)
    """

    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"


@unique
class UserRole(StrEnum):
    """
    Global role for access control (RBAC).

    Roles are hierarchical — each higher role inherits all permissions
    of the roles below it.

    Hierarchy (highest to lowest):
    BOT_OWNER > SUPER_ADMIN > GROUP_OWNER > ADMIN > MODERATOR > MEMBER > GUEST
    """

    BOT_OWNER = "bot_owner"
    SUPER_ADMIN = "super_admin"
    GROUP_OWNER = "group_owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
    GUEST = "guest"

    @property
    def level(self) -> int:
        """
        Return numeric privilege level for comparison.

        Higher number = higher privilege.
        """
        levels: dict[str, int] = {
            "guest": 0,
            "member": 10,
            "moderator": 20,
            "admin": 30,
            "group_owner": 40,
            "super_admin": 50,
            "bot_owner": 60,
        }
        return levels[self.value]

    def has_permission(self, required: "UserRole") -> bool:
        """Check if this role meets or exceeds the required role level."""
        return self.level >= required.level


@unique
class EventType(StrEnum):
    """
    Types of member events tracked in the audit log.

    Each event type corresponds to a specific action that occurred
    in a group, whether user-initiated or admin-initiated.
    """

    JOIN = "join"
    LEAVE = "leave"
    KICK = "kick"
    BAN = "ban"
    UNBAN = "unban"
    PROMOTE = "promote"
    DEMOTE = "demote"
    MUTE = "mute"
    UNMUTE = "unmute"
    WARN = "warn"
    REJOIN = "rejoin"
    BOT_ADDED = "bot_added"
    BOT_REMOVED = "bot_removed"
    INVITE_LINK_CREATED = "invite_link_created"
    INVITE_LINK_REVOKED = "invite_link_revoked"
    SETTINGS_CHANGED = "settings_changed"


@unique
class NotificationType(StrEnum):
    """
    Types of notifications sent by the bot.

    Each type maps to a specific event that triggers a notification
    to group admins, the group owner, or the bot owner.
    """

    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    MEMBER_KICKED = "member_kicked"
    ADMIN_CHANGED = "admin_changed"
    INVITE_LINK_CREATED = "invite_link_created"
    INVITE_LINK_REVOKED = "invite_link_revoked"
    BOT_ADDED = "bot_added"
    BOT_REMOVED = "bot_removed"
    MILESTONE_REACHED = "milestone_reached"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SPAM_DETECTED = "spam_detected"
    FLOOD_DETECTED = "flood_detected"
    DAILY_REPORT = "daily_report"
    WEEKLY_REPORT = "weekly_report"
    MONTHLY_REPORT = "monthly_report"


@unique
class ReportPeriod(StrEnum):
    """
    Time periods for generating statistical reports.
    """

    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    TOTAL = "total"
    CUSTOM = "custom"


@unique
class ExportFormat(StrEnum):
    """
    Supported export file formats for reports.
    """

    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PDF = "pdf"


@unique
class Language(StrEnum):
    """
    Supported languages for internationalization (i18n).

    The bot auto-detects the user's language from their Telegram
    client settings, with English as the fallback.
    """

    EN = "en"
    UZ = "uz"
    RU = "ru"

    @classmethod
    def from_telegram_code(cls, code: str | None) -> "Language":
        """
        Map a Telegram language_code to a supported Language.

        Telegram sends ISO 639-1 codes (e.g., 'en', 'ru', 'uz').
        Falls back to English for unsupported codes.

        Args:
            code: The Telegram language_code string, or None.

        Returns:
            The matched Language enum value.
        """
        if code is None:
            return cls.EN

        code_lower = code.lower().strip()

        # Direct matches
        mapping: dict[str, Language] = {
            "en": cls.EN,
            "uz": cls.UZ,
            "ru": cls.RU,
        }

        # Try direct match first
        if code_lower in mapping:
            return mapping[code_lower]

        # Try prefix match (e.g., 'en-US' -> 'en')
        prefix = code_lower.split("-")[0].split("_")[0]
        if prefix in mapping:
            return mapping[prefix]

        # Default to English
        return cls.EN
