from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.messaging.application.use_cases import (
    ConversationParticipation,
    ListConversationsUseCase,
    ReadMessagesUseCase,
    SendMessageUseCase,
    StartConversationUseCase,
)
from app.features.messaging.domain.repositories import (
    ConversationRepositoryProtocol,
    MessageRepositoryProtocol,
)
from app.features.messaging.infrastructure.persistence.repositories import (
    SqlAlchemyConversationRepository,
    SqlAlchemyMessageRepository,
)
from app.features.notifications.presentation.dependencies import get_notifier
from app.features.veterinarians.domain.repositories import VetProfileRepositoryProtocol
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


def get_start_conversation_use_case(
    conversations: ConversationRepositoryProtocol = Depends(get_conversation_repository),
    vets: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
) -> StartConversationUseCase:
    return StartConversationUseCase(conversations, vets)


def get_list_conversations_use_case(
    conversations: ConversationRepositoryProtocol = Depends(get_conversation_repository),
    messages: MessageRepositoryProtocol = Depends(get_message_repository),
) -> ListConversationsUseCase:
    return ListConversationsUseCase(conversations, messages)


def get_read_messages_use_case(
    participation: ConversationParticipation = Depends(get_conversation_participation),
    messages: MessageRepositoryProtocol = Depends(get_message_repository),
) -> ReadMessagesUseCase:
    return ReadMessagesUseCase(participation, messages)


def get_send_message_use_case(
    participation: ConversationParticipation = Depends(get_conversation_participation),
    conversations: ConversationRepositoryProtocol = Depends(get_conversation_repository),
    messages: MessageRepositoryProtocol = Depends(get_message_repository),
    notifier: NotifierProtocol = Depends(get_notifier),
) -> SendMessageUseCase:
    return SendMessageUseCase(participation, conversations, messages, notifier)
