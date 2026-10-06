from datetime import datetime, timezone

from app.core.exceptions import ValidationException
from app.features.auth.application.commands.create_client.create_client_command import (
    CreateClientCommand,
)
from app.features.auth.application.dtos.user_output_dto import UserOutputDTO
from app.features.auth.application.event_handlers.user_registered_event_handler import (
    UserRegisteredEventHandler,
)
from app.features.auth.application.interfaces.repositories.user_repository import (
    UserRepository,
)
from app.features.auth.application.interfaces.services.password_hasher import (
    PasswordHasher,
)
from app.features.auth.application.mappers.user_dto_mapper import UserDTOMapper
from app.features.auth.domain.entities.user import User
from app.features.auth.domain.enums.role import Role
from app.features.auth.domain.events.user_registered import (
    UserRegisteredDomainEvent,
)
from app.features.auth.domain.exceptions import UserAlreadyExistsError


class CreateClientCommandHandler:
    def __init__(
        self,
        user_repo: UserRepository,
        hasher: PasswordHasher,
        event_handler: UserRegisteredEventHandler | None = None,
    ):
        self._user_repo = user_repo
        self._hasher = hasher
        self._event_handler = event_handler or UserRegisteredEventHandler()

    async def handle(self, command: CreateClientCommand) -> UserOutputDTO:
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
        new_user = User(
            id=None,
            email=email,
            hashed_password=hashed_password,
            role=Role.CLIENT,
            full_name=command.full_name,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        saved = await self._user_repo.create(new_user)

        event = UserRegisteredDomainEvent(
            user_id=saved.id,
            email=saved.email,
            full_name=saved.full_name,
            occurred_at=now,
        )
        await self._event_handler.handle(event)

        return UserDTOMapper.to_output_dto(saved)
