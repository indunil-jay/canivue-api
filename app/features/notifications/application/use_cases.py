from collections.abc import Sequence
from dataclasses import dataclass

from app.features.notifications.domain.entities import Notification
from app.features.notifications.domain.repositories import (
    NotificationNotFoundError,
    NotificationRepositoryProtocol,
)
from app.shared.actor import Actor
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


@dataclass(frozen=True)
class NotificationInbox:
    items: Sequence[Notification]
    unread_count: int


class GetInboxUseCase:
    def __init__(self, notifications: NotificationRepositoryProtocol):
        self._notifications = notifications

    async def execute(self, actor: Actor, limit: int = 100) -> NotificationInbox:
        return NotificationInbox(
            items=await self._notifications.list_for_user(actor.id, limit),
            unread_count=await self._notifications.count_unread(actor.id),
        )


class MarkNotificationReadUseCase:
    def __init__(self, notifications: NotificationRepositoryProtocol):
        self._notifications = notifications

    async def execute(self, actor: Actor, notification_id: str) -> int:
        if await self._notifications.get_for_user(actor.id, notification_id) is None:
            raise NotificationNotFoundError()
        await self._notifications.mark_read(actor.id, notification_id)
        return await self._notifications.count_unread(actor.id)


class MarkAllNotificationsReadUseCase:
    def __init__(self, notifications: NotificationRepositoryProtocol):
        self._notifications = notifications

    async def execute(self, actor: Actor) -> int:
        await self._notifications.mark_read(actor.id)
        return 0
