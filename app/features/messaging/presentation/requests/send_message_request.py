from pydantic import BaseModel, Field

from app.features.messaging.domain.enums.message_kind import MessageKind


class SendMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    kind: MessageKind = MessageKind.TEXT
