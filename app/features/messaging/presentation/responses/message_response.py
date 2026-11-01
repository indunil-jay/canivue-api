from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.messaging.domain.enums.message_kind import MessageKind
from app.features.messaging.domain.enums.message_sender import MessageSender
from app.features.messaging.domain.enums.message_status import MessageStatus


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    sender: MessageSender
    text: str
    timestamp: datetime = Field(validation_alias="created_at")
    status: MessageStatus
    kind: MessageKind
