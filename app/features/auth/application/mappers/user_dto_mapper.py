from app.features.auth.application.dtos.user_output_dto import UserOutputDTO
from app.features.auth.domain.entities.user import User


class UserDTOMapper:
    @staticmethod
    def to_output_dto(entity: User) -> UserOutputDTO:
        return UserOutputDTO(
            id=entity.id,
            email=entity.email,
            role=entity.role,
            full_name=entity.full_name,
            is_active=entity.is_active,
            permissions=entity.permissions,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
