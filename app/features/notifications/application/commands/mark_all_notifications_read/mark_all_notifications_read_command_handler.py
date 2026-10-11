from app.features.notifications.application.commands.mark_all_notifications_read.mark_all_notifications_read_command import (
    MarkAllNotificationsReadCommand,
)
from app.features.notifications.application.interfaces.repositories.notification_repository import (
    NotificationRepositoryProtocol,
)


class MarkAllNotificationsReadCommandHandler:
    def __init__(self, notifications: NotificationRepositoryProtocol):
        self._notifications = notifications

    async def handle(self, command: MarkAllNotificationsReadCommand) -> int:
        await self._notifications.mark_read(command.actor.id)
        return 0
