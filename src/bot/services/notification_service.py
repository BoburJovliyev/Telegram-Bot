"""
Notification Service.

Handles queuing and formatting notifications to group admins
or the bot owner. Supports rate limiting and retries.
"""

from bot.services.base import BaseService


class NotificationService(BaseService):
    """Business logic for dispatching internal bot notifications."""

    async def queue_notification(
        self,
        user_id: int,
        notification_type: str,
        message_text: str,
        group_id: int | None = None,
    ) -> None:
        """
        Queue a notification to be sent.
        
        The actual sending is typically handled by a background worker
        (via APScheduler) to ensure we don't block the update handler
        and to properly manage Telegram's rate limits.
        """
        self.logger.info(
            "Queueing notification",
            user_id=user_id,
            type=notification_type,
            group_id=group_id
        )

        async with self.uow as uow:
            # We don't have a direct repo method for insert-only on Notification,
            # so we use the generic create method from BaseRepository.
            await uow.notifications.create(
                user_id=user_id,
                group_id=group_id,
                notification_type=notification_type,
                message_text=message_text,
                is_sent=False,
                retry_count=0,
            )
            
            await uow.commit()

    async def notify_admins(
        self,
        group_id: int,
        notification_type: str,
        message_text: str,
    ) -> None:
        """
        Queue a notification for all active admins of a group.
        """
        self.logger.info(
            "Queueing admin broadcast",
            group_id=group_id,
            type=notification_type
        )

        async with self.uow as uow:
            admins = await uow.admins.get_active_admins(group_id)
            
            for admin in admins:
                if admin.user.is_bot:
                    continue
                    
                await uow.notifications.create(
                    user_id=admin.user_id,
                    group_id=group_id,
                    notification_type=notification_type,
                    message_text=message_text,
                    is_sent=False,
                    retry_count=0,
                )
                
            await uow.commit()
