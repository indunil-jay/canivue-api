from collections.abc import Sequence
from typing import Protocol

from app.features.notifications.domain.entities.notification import Notification


class NotificationRepositoryProtocol(Protocol):
    async def create(self, entity: Notification) -> Notification: ...

    async def get_for_user(self, user_id: int, notification_id: str) -> Notification | None: ...

    async def list_for_user(self, user_id: int, limit: int) -> Sequence[Notification]: ...

    async def count_unread(self, user_id: int) -> int: ...

    async def mark_read(self, user_id: int, notification_id: str | None = None) -> None:
        """Marks one notification read, or all of the user's when no id is given."""
        ...
