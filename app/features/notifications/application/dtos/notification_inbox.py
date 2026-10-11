from collections.abc import Sequence
from dataclasses import dataclass

from app.features.notifications.domain.entities.notification import Notification


@dataclass(frozen=True)
class NotificationInbox:
    items: Sequence[Notification]
    unread_count: int
