from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.shared.notifier import NotificationType


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    message: str
    timestamp: datetime = Field(validation_alias="created_at")
    type: NotificationType
    dog_name: str
    is_read: bool
    action_label: str | None
