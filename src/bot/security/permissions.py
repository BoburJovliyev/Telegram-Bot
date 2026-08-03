"""
Role-Based Access Control (RBAC) engine.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import UserRole
from bot.models.admin import GroupAdmin
from bot.models.group import Group
from bot.config import get_settings


class PermissionsEngine:
    """
    Verifies user permissions within a group context.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    async def get_user_role(self, group_id: int, user_id: int) -> UserRole:
        """
        Determine the highest role a user has in a specific group.
        """
        # Check if user is the global bot owner
        if user_id == self.settings.bot_owner_id:
            return UserRole.BOT_OWNER

        # Check if user is a global super admin
        if user_id in self.settings.super_admin_ids:
            return UserRole.SUPER_ADMIN

        # Check group-specific roles
        group = (await self.session.execute(
            select(Group).where(Group.id == group_id)
        )).scalar_one_or_none()

        if not group:
            return UserRole.MEMBER

        if group.owner_id == user_id:
            return UserRole.GROUP_OWNER

        # Check if they are a registered admin in our DB
        admin_record = (await self.session.execute(
            select(GroupAdmin).where(
                GroupAdmin.group_id == group_id,
                GroupAdmin.user_id == user_id
            )
        )).scalar_one_or_none()

        if admin_record:
            if admin_record.role == UserRole.ADMIN.value:
                return UserRole.ADMIN
            if admin_record.role == UserRole.MODERATOR.value:
                return UserRole.MODERATOR

        return UserRole.MEMBER

    async def has_permission(self, group_id: int, user_id: int, required_role: UserRole) -> bool:
        """
        Check if a user meets or exceeds a required role.
        """
        actual_role = await self.get_user_role(group_id, user_id)
        
        # Define hierarchy (lower index = higher privilege)
        hierarchy = [
            UserRole.BOT_OWNER,
            UserRole.SUPER_ADMIN,
            UserRole.GROUP_OWNER,
            UserRole.ADMIN,
            UserRole.MODERATOR,
            UserRole.MEMBER,
        ]
        
        actual_index = hierarchy.index(actual_role)
        required_index = hierarchy.index(required_role)
        
        return actual_index <= required_index
