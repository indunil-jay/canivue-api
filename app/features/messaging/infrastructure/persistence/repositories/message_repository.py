from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import update

from app.core.dataclass_repository import DataclassRepository
from app.features.messaging.application.interfaces.repositories.message_repository import (
    MessageRepositoryProtocol,
)
from app.features.messaging.domain.entities.message import Message
from app.features.messaging.domain.enums.message_sender import MessageSender
from app.features.messaging.domain.enums.message_status import MessageStatus
from app.features.messaging.infrastructure.persistence.models.message_model import MessageModel

# Statuses that may still be advanced to the key.
_BEHIND = {
    MessageStatus.DELIVERED: [MessageStatus.SENT.value],
    MessageStatus.READ: [MessageStatus.SENT.value, MessageStatus.DELIVERED.value],
}


class SqlAlchemyMessageRepository(
    DataclassRepository[Message, MessageModel], MessageRepositoryProtocol
):
    _model_cls = MessageModel
    _entity_cls = Message

    async def list_for_conversation(
        self, conversation_id: str, after: datetime | None, limit: int
    ) -> Sequence[Message]:
        where = [MessageModel.conversation_id == conversation_id]
        if after is not None:
            where.append(MessageModel.created_at > after)
        return await self.find(*where, order_by=MessageModel.created_at, limit=limit)

    async def count_unread_from(self, conversation_id: str, sender: MessageSender) -> int:
        return await self.count(
            MessageModel.conversation_id == conversation_id,
            MessageModel.sender == sender.value,
            MessageModel.status != MessageStatus.READ.value,
        )

    async def advance_status(
        self, conversation_ids: Sequence[str], sender: MessageSender, to: MessageStatus
    ) -> None:
        await self._session.execute(
            update(MessageModel)
            .where(
                MessageModel.conversation_id.in_(conversation_ids),
                MessageModel.sender == sender.value,
                MessageModel.status.in_(_BEHIND[to]),
            )
            .values(status=to.value)
        )
        await self._session.flush()
