from app.features.notifications.application.interfaces.repositories.notification_repository import (
    NotificationRepositoryProtocol,
)
from app.features.notifications.domain.entities.notification import Notification
from app.shared.notifier import NotificationType, NotifierProtocol


class StoredNotifier(NotifierProtocol):
    """Records notifications for later reading. There is no push delivery."""

    def __init__(self, notifications: NotificationRepositoryProtocol):
        self._notifications = notifications

    async def notify(
        self,
        user_id: int,
        type: NotificationType,
        title: str,
        message: str,
        dog_name: str = "",
        action_label: str | None = None,
    ) -> None:
        await self._notifications.create(
            Notification(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                dog_name=dog_name,
                action_label=action_label,
            )
        )
