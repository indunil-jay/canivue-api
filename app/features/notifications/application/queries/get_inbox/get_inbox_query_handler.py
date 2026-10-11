from app.features.notifications.application.dtos.notification_inbox import NotificationInbox
from app.features.notifications.application.interfaces.repositories.notification_repository import (
    NotificationRepositoryProtocol,
)
from app.features.notifications.application.queries.get_inbox.get_inbox_query import GetInboxQuery


class GetInboxQueryHandler:
    def __init__(self, notifications: NotificationRepositoryProtocol):
        self._notifications = notifications

    async def handle(self, query: GetInboxQuery) -> NotificationInbox:
        return NotificationInbox(
            items=await self._notifications.list_for_user(query.actor.id, query.limit),
            unread_count=await self._notifications.count_unread(query.actor.id),
        )
