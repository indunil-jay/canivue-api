from dataclasses import dataclass

from app.features.messaging.domain.entities.conversation import Conversation


@dataclass(frozen=True)
class ConversationView:
    conversation: Conversation
    unread_count: int
