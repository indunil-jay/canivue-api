from app.features.messaging.application.dtos.conversation_output_dto import ConversationOutputDTO
from app.features.messaging.domain.entities.conversation import Conversation


class ConversationDTOMapper:
    @staticmethod
    def to_output_dto(entity: Conversation) -> ConversationOutputDTO:
        return ConversationOutputDTO(
            id=entity.id,
            owner_id=entity.owner_id,
            owner_name=entity.owner_name,
            vet_id=entity.vet_id,
            vet_user_id=entity.vet_user_id,
            vet_name=entity.vet_name,
            last_message_preview=entity.last_message_preview,
            last_message_at=entity.last_message_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
