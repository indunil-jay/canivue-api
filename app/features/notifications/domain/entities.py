from dataclasses import dataclass

from app.shared.entity import BaseEntity
from app.shared.notifier import NotificationType


@dataclass
class Notification(BaseEntity):
    user_id: int = 0
    type: NotificationType = NotificationType.AI_HEALTH_ALERT
    title: str = ""
    message: str = ""
    dog_name: str = ""
    action_label: str | None = None
    is_read: bool = False
