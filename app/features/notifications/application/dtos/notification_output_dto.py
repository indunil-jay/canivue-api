from dataclasses import dataclass
from datetime import datetime

from app.shared.notifier import NotificationType


@dataclass(frozen=True)
class NotificationOutputDTO:
    id: str
    user_id: int
    type: NotificationType
    title: str
    message: str
    dog_name: str
    action_label: str | None
    is_read: bool
    created_at: datetime
    updated_at: datetime | None
