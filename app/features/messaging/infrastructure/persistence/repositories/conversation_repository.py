from collections.abc import Sequence

from sqlalchemy import or_

from app.core.dataclass_repository import DataclassRepository
from app.features.messaging.application.interfaces.repositories.conversation_repository import (
    ConversationRepositoryProtocol,
)
from app.features.messaging.domain.entities.conversation import Conversation
from app.features.messaging.infrastructure.persistence.models.conversation_model import (
    ConversationModel,
)


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
