from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.features.messaging.domain.entities import (
    Conversation,
    ConversationNotFoundError,
    Message,
    MessageKind,
    MessageSender,
    MessageStatus,
    SummaryNotAllowedError,
)
from app.features.messaging.domain.repositories import (
    ConversationRepositoryProtocol,
    MessageRepositoryProtocol,
)
from app.features.veterinarians.domain.exceptions import VeterinarianNotFoundError
from app.features.veterinarians.domain.repositories import VetProfileRepositoryProtocol
from app.shared.actor import Actor
from app.shared.entity import _utc_now
from app.shared.notifier import NotificationType, NotifierProtocol

PREVIEW_LENGTH = 120


@dataclass(frozen=True)
class ConversationView:
    conversation: Conversation
    unread_count: int


def _other(side: MessageSender) -> MessageSender:
    return MessageSender.VET if side == MessageSender.OWNER else MessageSender.OWNER


class ConversationParticipation:
    def __init__(self, conversations: ConversationRepositoryProtocol):
        self._conversations = conversations

    async def load(self, actor: Actor, conversation_id: str) -> tuple[Conversation, MessageSender]:
        conversation = await self._conversations.get_by_id(conversation_id)
        side = conversation.side_of(actor.id) if conversation else None
        if conversation is None or side is None:
            raise ConversationNotFoundError()
        return conversation, side


class StartConversationUseCase:
    def __init__(
        self, conversations: ConversationRepositoryProtocol, vets: VetProfileRepositoryProtocol
    ):
        self._conversations = conversations
        self._vets = vets

    async def execute(self, actor: Actor, vet_id: str) -> ConversationView:
        vet = await self._vets.get_by_id(vet_id)
        if vet is None or not vet.verified or vet.user_id == actor.id:
            raise VeterinarianNotFoundError()
        existing = await self._conversations.get_for_pair(actor.id, vet.id)
        conversation = existing or await self._conversations.create(
            Conversation(
                owner_id=actor.id,
                owner_name=actor.display_name,
                vet_id=vet.id,
                vet_user_id=vet.user_id,
                vet_name=vet.name,
            )
        )
        return ConversationView(conversation, unread_count=0)


class ListConversationsUseCase:
    def __init__(
        self, conversations: ConversationRepositoryProtocol, messages: MessageRepositoryProtocol
    ):
        self._conversations = conversations
        self._messages = messages

    async def execute(self, actor: Actor) -> list[ConversationView]:
        conversations = await self._conversations.list_for_user(actor.id)
        views = []
        for conversation in conversations:
            incoming = _other(conversation.side_of(actor.id))
            # Seeing the conversation list is what "delivered" means for the other side.
            await self._messages.advance_status(
                [conversation.id], incoming, MessageStatus.DELIVERED
            )
            unread = await self._messages.count_unread_from(conversation.id, incoming)
            views.append(ConversationView(conversation, unread))
        return views


class ReadMessagesUseCase:
    def __init__(
        self, participation: ConversationParticipation, messages: MessageRepositoryProtocol
    ):
        self._participation = participation
        self._messages = messages

    async def execute(
        self, actor: Actor, conversation_id: str, after: datetime | None = None, limit: int = 200
    ) -> Sequence[Message]:
        conversation, side = await self._participation.load(actor, conversation_id)
        await self._messages.advance_status([conversation.id], _other(side), MessageStatus.READ)
        return await self._messages.list_for_conversation(conversation.id, after, limit)


class SendMessageUseCase:
    def __init__(
        self,
        participation: ConversationParticipation,
        conversations: ConversationRepositoryProtocol,
        messages: MessageRepositoryProtocol,
        notifier: NotifierProtocol,
    ):
        self._participation = participation
        self._conversations = conversations
        self._messages = messages
        self._notifier = notifier

    async def execute(
        self, actor: Actor, conversation_id: str, text: str, kind: MessageKind = MessageKind.TEXT
    ) -> Message:
        conversation, side = await self._participation.load(actor, conversation_id)
        if kind == MessageKind.CONSULTATION_SUMMARY and side != MessageSender.VET:
            raise SummaryNotAllowedError()

        message = await self._messages.create(
            Message(conversation_id=conversation.id, sender=side, text=text.strip(), kind=kind)
        )
        conversation.last_message_preview = message.text[:PREVIEW_LENGTH]
        conversation.last_message_at = message.created_at
        conversation.updated_at = _utc_now()
        await self._conversations.update(conversation)

        sender_name = (
            conversation.vet_name if side == MessageSender.VET else conversation.owner_name
        )
        await self._notifier.notify(
            conversation.other_user_id(side),
            NotificationType.VET_MESSAGE,
            f"New message from {sender_name}",
            message.text[:PREVIEW_LENGTH],
            action_label="Open Chat",
        )
        return message
