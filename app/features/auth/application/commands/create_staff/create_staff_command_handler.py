from datetime import datetime, timezone

from app.features.auth.application.commands.create_staff.create_staff_command import (
    CreateStaffCommand,
)
from app.features.auth.application.dtos.user_output_dto import UserOutputDTO
from app.features.auth.application.event_handlers.staff_user_created_event_handler import (
    StaffUserCreatedEventHandler,
)
from app.features.auth.application.interfaces.repositories.user_repository import (
    UserRepository,
)
from app.features.auth.application.interfaces.services.password_hasher import (
    PasswordHasher,
)
from app.features.auth.application.mappers.user_dto_mapper import UserDTOMapper
from app.features.auth.domain.entities.user import User
from app.features.auth.domain.events.staff_user_created import (
    StaffUserCreatedDomainEvent,
)
from app.features.auth.domain.exceptions import (
    InvalidEmailError,
    UserAlreadyExistsError,
    WeakPasswordError,
)


class CreateStaffCommandHandler:
    def __init__(
        self,
        user_repo: UserRepository,
        hasher: PasswordHasher,
        event_handler: StaffUserCreatedEventHandler | None = None,
    ):
        self._user_repo = user_repo
        self._hasher = hasher
        self._event_handler = event_handler or StaffUserCreatedEventHandler()

    async def handle(self, command: CreateStaffCommand) -> UserOutputDTO:
        email = command.email.strip().lower()
        if not email or "@" not in email:
            raise InvalidEmailError()

        if len(command.password) < 8:
            raise WeakPasswordError()

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

        event = StaffUserCreatedDomainEvent(
            user_id=saved.id,
            email=saved.email,
            role=saved.role,
            full_name=saved.full_name,
            occurred_at=now,
        )
        await self._event_handler.handle(event)

        return UserDTOMapper.to_output_dto(saved)
