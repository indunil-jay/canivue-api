from app.core.exceptions import ValidationException
from app.features.auth.application.dtos import RegisterClientInputDTO, UserOutputDTO
from app.features.auth.domain.entities import User
from app.features.auth.domain.exceptions import UserAlreadyExistsError
from app.features.auth.domain.protocols import PasswordHasherProtocol, UserRepositoryProtocol


class RegisterClientUseCase:
    """Use case to handle self-registration of client accounts."""

    def __init__(self, user_repo: UserRepositoryProtocol, hasher: PasswordHasherProtocol):
        self._user_repo = user_repo
        self._hasher = hasher

    async def execute(self, dto: RegisterClientInputDTO) -> UserOutputDTO:
        email = dto.email.strip().lower()
        if not email or "@" not in email:
            raise ValidationException("A valid email address is required.")

        if len(dto.password) < 8:
            raise ValidationException("Password must be at least 8 characters long.")

        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError(email)

        hashed_password = self._hasher.hash(dto.password)
        new_user = User.create_client(
            email=email,
            hashed_password=hashed_password,
            full_name=dto.full_name,
        )

        saved_user = await self._user_repo.create(new_user)

        return UserOutputDTO(
            id=saved_user.id,
            email=saved_user.email,
            role=saved_user.role,
            full_name=saved_user.full_name,
            is_active=saved_user.is_active,
            created_at=saved_user.created_at,
            updated_at=saved_user.updated_at,
        )
