from collections.abc import Sequence

from app.features.messaging.application.commands.read_messages.read_messages_command import (
    ReadMessagesCommand,
)
from app.features.messaging.application.interfaces.repositories.message_repository import (
    MessageRepositoryProtocol,
)
from app.features.messaging.application.services.conversation_participation import (
    ConversationParticipation,
)
from app.features.messaging.application.services.other_side import other_side
from app.features.messaging.domain.entities.message import Message
from app.features.messaging.domain.enums.message_status import MessageStatus


class ReadMessagesCommandHandler:
    def __init__(
        self, participation: ConversationParticipation, messages: MessageRepositoryProtocol
    ):
        self._participation = participation
        self._messages = messages

    async def handle(self, command: ReadMessagesCommand) -> Sequence[Message]:
        conversation, side = await self._participation.load(command.actor, command.conversation_id)
        await self._messages.advance_status([conversation.id], other_side(side), MessageStatus.READ)
        return await self._messages.list_for_conversation(
            conversation.id, command.after, command.limit
        )
