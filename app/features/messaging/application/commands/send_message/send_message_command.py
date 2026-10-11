from dataclasses import dataclass

from app.features.messaging.domain.enums.message_kind import MessageKind
from app.shared.actor import Actor


@dataclass(frozen=True)
class SendMessageCommand:
    actor: Actor
    conversation_id: str
    text: str
    kind: MessageKind = MessageKind.TEXT
