from app.features.notifications.application.dtos.notification_output_dto import (
    NotificationOutputDTO,
)
from app.features.notifications.domain.entities.notification import Notification


class NotificationDTOMapper:
    @staticmethod
    def to_output_dto(entity: Notification) -> NotificationOutputDTO:
        return NotificationOutputDTO(
            id=entity.id,
            user_id=entity.user_id,
            type=entity.type,
            title=entity.title,
            message=entity.message,
            dog_name=entity.dog_name,
            action_label=entity.action_label,
            is_read=entity.is_read,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
