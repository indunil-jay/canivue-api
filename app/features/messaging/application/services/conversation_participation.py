from app.features.messaging.application.interfaces.repositories.conversation_repository import (
    ConversationRepositoryProtocol,
)
from app.features.messaging.domain.entities.conversation import Conversation
from app.features.messaging.domain.enums.message_sender import MessageSender
from app.features.messaging.domain.exceptions import ConversationNotFoundError
from app.shared.actor import Actor


class ConversationParticipation:
    def __init__(self, conversations: ConversationRepositoryProtocol):
        self._conversations = conversations

    async def load(self, actor: Actor, conversation_id: str) -> tuple[Conversation, MessageSender]:
        conversation = await self._conversations.get_by_id(conversation_id)
        side = conversation.side_of(actor.id) if conversation else None
        if conversation is None or side is None:
            raise ConversationNotFoundError()
        return conversation, side
