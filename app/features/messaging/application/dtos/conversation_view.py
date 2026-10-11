from dataclasses import dataclass

from app.features.messaging.application.dtos.conversation_output_dto import ConversationOutputDTO


@dataclass(frozen=True)
class ConversationView:
    conversation: ConversationOutputDTO
    unread_count: int
