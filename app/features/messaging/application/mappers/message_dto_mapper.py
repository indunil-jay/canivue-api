from app.features.messaging.application.dtos.message_output_dto import MessageOutputDTO
from app.features.messaging.domain.entities.message import Message


class MessageDTOMapper:
    @staticmethod
    def to_output_dto(entity: Message) -> MessageOutputDTO:
        return MessageOutputDTO(
            id=entity.id,
            conversation_id=entity.conversation_id,
            sender=entity.sender,
            text=entity.text,
            kind=entity.kind,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
