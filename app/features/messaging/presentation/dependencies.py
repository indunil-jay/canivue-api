from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.messaging.application.commands.read_messages.read_messages_command_handler import (
    ReadMessagesCommandHandler,
)
from app.features.messaging.application.commands.send_message.send_message_command_handler import (
    SendMessageCommandHandler,
)
from app.features.messaging.application.commands.start_conversation.start_conversation_command_handler import (
    StartConversationCommandHandler,
)
from app.features.messaging.application.interfaces.repositories.conversation_repository import (
    ConversationRepositoryProtocol,
)
from app.features.messaging.application.interfaces.repositories.message_repository import (
    MessageRepositoryProtocol,
)
from app.features.messaging.application.queries.list_conversations.list_conversations_query_handler import (
    ListConversationsQueryHandler,
)
from app.features.messaging.application.services.conversation_participation import (
    ConversationParticipation,
)
from app.features.messaging.infrastructure.persistence.repositories.conversation_repository import (
    SqlAlchemyConversationRepository,
)
from app.features.messaging.infrastructure.persistence.repositories.message_repository import (
    SqlAlchemyMessageRepository,
)
from app.features.notifications.presentation.dependencies import get_notifier
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.presentation.dependencies import get_vet_profile_repository
from app.shared.notifier import NotifierProtocol


def get_conversation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationRepositoryProtocol:
    return SqlAlchemyConversationRepository(session=session)


def get_message_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MessageRepositoryProtocol:
    return SqlAlchemyMessageRepository(session=session)


def get_conversation_participation(
    conversations: ConversationRepositoryProtocol = Depends(get_conversation_repository),
) -> ConversationParticipation:
    return ConversationParticipation(conversations)


def get_start_conversation_command_handler(
    conversations: ConversationRepositoryProtocol = Depends(get_conversation_repository),
    vets: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
) -> StartConversationCommandHandler:
    return StartConversationCommandHandler(conversations, vets)


def get_list_conversations_query_handler(
    conversations: ConversationRepositoryProtocol = Depends(get_conversation_repository),
    messages: MessageRepositoryProtocol = Depends(get_message_repository),
) -> ListConversationsQueryHandler:
    return ListConversationsQueryHandler(conversations, messages)


def get_read_messages_command_handler(
    participation: ConversationParticipation = Depends(get_conversation_participation),
    messages: MessageRepositoryProtocol = Depends(get_message_repository),
) -> ReadMessagesCommandHandler:
    return ReadMessagesCommandHandler(participation, messages)


def get_send_message_command_handler(
    participation: ConversationParticipation = Depends(get_conversation_participation),
    conversations: ConversationRepositoryProtocol = Depends(get_conversation_repository),
    messages: MessageRepositoryProtocol = Depends(get_message_repository),
    notifier: NotifierProtocol = Depends(get_notifier),
) -> SendMessageCommandHandler:
    return SendMessageCommandHandler(participation, conversations, messages, notifier)
