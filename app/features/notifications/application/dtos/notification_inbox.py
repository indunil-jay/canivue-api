from dataclasses import dataclass

from app.features.notifications.application.dtos.notification_output_dto import (
    NotificationOutputDTO,
)


@dataclass(frozen=True)
class NotificationInbox:
    items: list[NotificationOutputDTO]
    unread_count: int
