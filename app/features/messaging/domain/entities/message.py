from dataclasses import dataclass

from app.features.messaging.domain.enums.message_kind import MessageKind
from app.features.messaging.domain.enums.message_sender import MessageSender
from app.features.messaging.domain.enums.message_status import MessageStatus
from app.shared.entity import BaseEntity


@dataclass
class Message(BaseEntity):
    conversation_id: str = ""
    sender: MessageSender = MessageSender.OWNER
    text: str = ""
    kind: MessageKind = MessageKind.TEXT
    status: MessageStatus = MessageStatus.SENT
