from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.features.auth.application.dtos.user_output_dto import UserOutputDTO
from app.features.auth.application.interfaces.repositories.user_repository import UserRepository
from app.features.auth.application.mappers.user_dto_mapper import UserDTOMapper
from app.features.auth.domain.exceptions import UserNotFoundError

PROFILE_FIELDS = ("full_name", "phone", "address", "emergency_contact")


@dataclass(frozen=True)
class UpdateProfileCommand:
    user_id: int
    changes: dict[str, Any] = field(default_factory=dict)
    privacy_changes: dict[str, bool] = field(default_factory=dict)


class UpdateProfileCommandHandler:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def handle(self, command: UpdateProfileCommand) -> UserOutputDTO:
        user = await self._user_repo.get_by_id(command.user_id)
        if not user:
            raise UserNotFoundError()

        for name, value in command.changes.items():
            if name in PROFILE_FIELDS:
                setattr(user, name, value)
        user.privacy = user.privacy.updated(command.privacy_changes)
        user.updated_at = datetime.now(timezone.utc)
        return UserDTOMapper.to_output_dto(await self._user_repo.update(user))
