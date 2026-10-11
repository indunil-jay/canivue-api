from app.features.messaging.application.commands.send_message.send_message_command import (
    SendMessageCommand,
)
from app.features.messaging.application.dtos.message_output_dto import MessageOutputDTO
from app.features.messaging.application.interfaces.repositories.conversation_repository import (
    ConversationRepositoryProtocol,
)
from app.features.messaging.application.interfaces.repositories.message_repository import (
    MessageRepositoryProtocol,
)
from app.features.messaging.application.mappers.message_dto_mapper import MessageDTOMapper
from app.features.messaging.application.services.conversation_participation import (
    ConversationParticipation,
)
from app.features.messaging.domain.entities.message import Message
from app.features.messaging.domain.enums.message_kind import MessageKind
from app.features.messaging.domain.enums.message_sender import MessageSender
from app.features.messaging.domain.exceptions import SummaryNotAllowedError
from app.shared.entity import _utc_now
from app.shared.notifier import NotificationType, NotifierProtocol

PREVIEW_LENGTH = 120


class SendMessageCommandHandler:
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

    async def handle(self, command: SendMessageCommand) -> MessageOutputDTO:
        conversation, side = await self._participation.load(command.actor, command.conversation_id)
        if command.kind == MessageKind.CONSULTATION_SUMMARY and side != MessageSender.VET:
            raise SummaryNotAllowedError()

        message = await self._messages.create(
            Message(
                conversation_id=conversation.id,
                sender=side,
                text=command.text.strip(),
                kind=command.kind,
            )
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
        return MessageDTOMapper.to_output_dto(message)
