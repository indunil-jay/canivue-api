from datetime import datetime, timezone

from app.core.exceptions import ValidationException
from app.features.auth.application.commands.dtos import CreateStaffUserCommand
from app.features.auth.application.common_dtos import UserOutputDTO
from app.features.auth.domain.entities import User
from app.features.auth.domain.exceptions import UserAlreadyExistsError
from app.features.auth.domain.repositories import UserRepository
from app.features.auth.domain.services import PasswordHasher


class CreateStaffUserUseCase:
    """Command Use Case allowing administrators to onboard staff users (VET or ADMIN)."""

    def __init__(self, user_repo: UserRepository, hasher: PasswordHasher):
        self._user_repo = user_repo
        self._hasher = hasher

    async def execute(self, command: CreateStaffUserCommand) -> UserOutputDTO:
        email = command.email.strip().lower()
        if not email or "@" not in email:
            raise ValidationException("A valid email address is required.")

        if len(command.password) < 8:
            raise ValidationException("Password must be at least 8 characters long.")

        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError(email)

        now = datetime.now(timezone.utc)
        hashed_password = self._hasher.hash(command.password)
        new_staff = User(
            id=None,
            email=email,
            hashed_password=hashed_password,
            role=command.role,
            full_name=command.full_name,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        saved = await self._user_repo.create(new_staff)
        return UserOutputDTO(
            id=saved.id,
            email=saved.email,
            role=saved.role,
            full_name=saved.full_name,
            is_active=saved.is_active,
            permissions=saved.permissions,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )
