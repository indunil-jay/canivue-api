from app.features.messaging.application.dtos.conversation_view import ConversationView
from app.features.messaging.application.interfaces.repositories.conversation_repository import (
    ConversationRepositoryProtocol,
)
from app.features.messaging.application.interfaces.repositories.message_repository import (
    MessageRepositoryProtocol,
)
from app.features.messaging.application.mappers.conversation_dto_mapper import ConversationDTOMapper
from app.features.messaging.application.queries.list_conversations.list_conversations_query import (
    ListConversationsQuery,
)
from app.features.messaging.application.services.other_side import other_side
from app.features.messaging.domain.enums.message_status import MessageStatus


class ListConversationsQueryHandler:
    def __init__(
        self, conversations: ConversationRepositoryProtocol, messages: MessageRepositoryProtocol
    ):
        self._conversations = conversations
        self._messages = messages

    async def handle(self, query: ListConversationsQuery) -> list[ConversationView]:
        conversations = await self._conversations.list_for_user(query.actor.id)
        views = []
        for conversation in conversations:
            incoming = other_side(conversation.side_of(query.actor.id))
            # Seeing the conversation list is what "delivered" means for the other side.
            await self._messages.advance_status(
                [conversation.id], incoming, MessageStatus.DELIVERED
            )
            unread = await self._messages.count_unread_from(conversation.id, incoming)
            views.append(
                ConversationView(ConversationDTOMapper.to_output_dto(conversation), unread)
            )
        return views
