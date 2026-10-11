from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from app.features.messaging.domain.entities import (
    Conversation,
    Message,
    MessageSender,
    MessageStatus,
)


class ConversationRepositoryProtocol(Protocol):
    async def get_by_id(self, entity_id: str) -> Conversation | None: ...

    async def get_for_pair(self, owner_id: int, vet_id: str) -> Conversation | None: ...

    async def list_for_user(self, user_id: int) -> Sequence[Conversation]: ...

    async def create(self, entity: Conversation) -> Conversation: ...

    async def update(self, entity: Conversation) -> Conversation: ...


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
