"""
Custom Aiogram filters for Role-Based Access Control.
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.core.enums import UserRole


class RoleFilter(BaseFilter):
    """
    Filter that checks if a user has the required role or higher.
    Relies on the ACLMiddleware to have injected 'user_role' into the context data.
    """
    def __init__(self, required_role: UserRole):
        self.required_role = required_role
        
        # Lower index = higher privilege
        self.hierarchy = [
            UserRole.BOT_OWNER,
            UserRole.SUPER_ADMIN,
            UserRole.GROUP_OWNER,
            UserRole.ADMIN,
            UserRole.MODERATOR,
            UserRole.MEMBER,
        ]

    async def __call__(self, message: Message, user_role: UserRole) -> bool:
        try:
            actual_index = self.hierarchy.index(user_role)
            required_index = self.hierarchy.index(self.required_role)
            return actual_index <= required_index
        except ValueError:
            return False
