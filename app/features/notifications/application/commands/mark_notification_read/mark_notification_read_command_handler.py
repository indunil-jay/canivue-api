from app.features.notifications.application.commands.mark_notification_read.mark_notification_read_command import (
    MarkNotificationReadCommand,
)
from app.features.notifications.application.interfaces.repositories.notification_repository import (
    NotificationRepositoryProtocol,
)
from app.features.notifications.domain.exceptions import NotificationNotFoundError


class MarkNotificationReadCommandHandler:
    def __init__(self, notifications: NotificationRepositoryProtocol):
        self._notifications = notifications

    async def handle(self, command: MarkNotificationReadCommand) -> int:
        if (
            await self._notifications.get_for_user(command.actor.id, command.notification_id)
            is None
        ):
            raise NotificationNotFoundError()
        await self._notifications.mark_read(command.actor.id, command.notification_id)
        return await self._notifications.count_unread(command.actor.id)
