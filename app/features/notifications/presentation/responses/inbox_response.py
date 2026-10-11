from pydantic import BaseModel, ConfigDict

from app.features.notifications.presentation.responses.notification_response import (
    NotificationResponse,
)


class InboxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[NotificationResponse]
    unread_count: int
