from dataclasses import dataclass
from datetime import datetime

from app.features.messaging.domain.enums.message_kind import MessageKind
from app.features.messaging.domain.enums.message_sender import MessageSender
from app.features.messaging.domain.enums.message_status import MessageStatus


@dataclass(frozen=True)
class MessageOutputDTO:
    id: str
    conversation_id: str
    sender: MessageSender
    text: str
    kind: MessageKind
    status: MessageStatus
    created_at: datetime
    updated_at: datetime | None
