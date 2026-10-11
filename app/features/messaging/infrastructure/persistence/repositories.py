from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import or_, update

from app.core.dataclass_repository import DataclassRepository
from app.features.dogs.domain.entities import Dog
from app.features.dogs.domain.repositories import PatientRegistryProtocol
from app.features.messaging.domain.entities import (
    Conversation,
    Message,
    MessageSender,
    MessageStatus,
)
from app.features.messaging.domain.repositories import (
    ConversationRepositoryProtocol,
    MessageRepositoryProtocol,
)
from app.features.messaging.infrastructure.persistence.models import (
    ConversationModel,
    MessageModel,
)

# Statuses that may still be advanced to the key.
_BEHIND = {
    MessageStatus.DELIVERED: [MessageStatus.SENT.value],
    MessageStatus.READ: [MessageStatus.SENT.value, MessageStatus.DELIVERED.value],
}


class SqlAlchemyConversationRepository(
    DataclassRepository[Conversation, ConversationModel], ConversationRepositoryProtocol
):
    _model_cls = ConversationModel
    _entity_cls = Conversation

    async def get_for_pair(self, owner_id: int, vet_id: str) -> Conversation | None:
        return await self.find_one(
            ConversationModel.owner_id == owner_id, ConversationModel.vet_id == vet_id
        )

    async def list_for_user(self, user_id: int) -> Sequence[Conversation]:
        return await self.find(
            or_(ConversationModel.owner_id == user_id, ConversationModel.vet_user_id == user_id),
            order_by=[
                ConversationModel.last_message_at.desc().nulls_last(),
                ConversationModel.created_at.desc(),
            ],
        )


class ConversationPatientRegistry(SqlAlchemyConversationRepository, PatientRegistryProtocol):
    """A Dog is a veterinarian's patient when its owner has a conversation with them."""

    async def is_patient(self, vet_user_id: int, dog: Dog) -> bool:
        linked = await self.count(
            ConversationModel.vet_user_id == vet_user_id, ConversationModel.owner_id == dog.owner_id
        )
        return linked > 0


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
