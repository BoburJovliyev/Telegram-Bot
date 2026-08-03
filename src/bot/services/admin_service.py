"""
Admin Validation Service.

Handles authorization checks against the GroupAdmin repository.
Used by middlewares and filters to restrict access to commands.
"""

from bot.core.enums import AdminRole
from bot.services.base import BaseService


class AdminService(BaseService):
    """Business logic for authorization and permissions."""

    async def is_admin(self, group_id: int, user_id: int) -> bool:
        """
        Check if a user is an active admin in the group.
        """
        async with self.uow as uow:
            admins = await uow.admins.get_active_admins(group_id)
            return any(admin.user_id == user_id for admin in admins)

    async def is_owner(self, group_id: int, user_id: int) -> bool:
        """
        Check if a user is the OWNER of the group.
        """
        async with self.uow as uow:
            admins = await uow.admins.get_active_admins(group_id)
            for admin in admins:
                if admin.user_id == user_id and admin.role == AdminRole.OWNER.value:
                    return True
            return False

    async def has_permission(self, group_id: int, user_id: int, permission: str) -> bool:
        """
        Check if an admin has a specific boolean permission.
        Always returns True for the group OWNER.
        """
        async with self.uow as uow:
            admins = await uow.admins.get_active_admins(group_id)
            
            for admin in admins:
                if admin.user_id == user_id:
                    # Owner implicitly has all permissions
                    if admin.role == AdminRole.OWNER.value:
                        return True
                        
                    # Check specific permission field
                    return getattr(admin, permission, False)
                    
            return False
