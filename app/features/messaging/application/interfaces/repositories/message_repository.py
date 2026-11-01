from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from app.features.messaging.domain.entities.message import Message
from app.features.messaging.domain.enums.message_sender import MessageSender
from app.features.messaging.domain.enums.message_status import MessageStatus


class MessageRepositoryProtocol(Protocol):
    async def create(self, entity: Message) -> Message: ...

    async def list_for_conversation(
        self, conversation_id: str, after: datetime | None, limit: int
    ) -> Sequence[Message]: ...

    async def count_unread_from(self, conversation_id: str, sender: MessageSender) -> int: ...

    async def advance_status(
        self, conversation_ids: Sequence[str], sender: MessageSender, to: MessageStatus
    ) -> None:
        """Moves that sender's messages forward to `to`; never moves a status backwards."""
        ...
