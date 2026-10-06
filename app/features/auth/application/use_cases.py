from app.core.exceptions import ValidationException
from app.features.auth.application.dtos import (
    LoginInputDTO,
    LoginOutputDTO,
    RegisterClientInputDTO,
    UserOutputDTO,
)
from app.features.auth.domain.entities import User
from app.features.auth.domain.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.features.auth.domain.protocols import (
    PasswordHasherProtocol,
    TokenServiceProtocol,
    UserRepositoryProtocol,
)


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


class LoginUseCase:
    """Use case to authenticate user credentials and issue tokens."""

    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        hasher: PasswordHasherProtocol,
        token_service: TokenServiceProtocol,
    ):
        self._user_repo = user_repo
        self._hasher = hasher
        self._token_service = token_service

    async def execute(self, dto: LoginInputDTO) -> LoginOutputDTO:
        email = dto.email.strip().lower()
        user = await self._user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError()

        if not self._hasher.verify(dto.password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountDisabledError()

        access_token = self._token_service.create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )
        refresh_token = self._token_service.create_refresh_token(
            subject=str(user.id),
        )

        user_dto = UserOutputDTO(
            id=user.id,
            email=user.email,
            role=user.role,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        return LoginOutputDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_dto,
        )


class GetCurrentUserUseCase:
    """Use case to retrieve active authenticated user by ID."""

    def __init__(self, user_repo: UserRepositoryProtocol):
        self._user_repo = user_repo

    async def execute(self, user_id: int) -> UserOutputDTO:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise InvalidCredentialsError("User account not found.")

        if not user.is_active:
            raise AccountDisabledError()

        return UserOutputDTO(
            id=user.id,
            email=user.email,
            role=user.role,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

