from datetime import datetime, timezone

from app.core.exceptions import ValidationException
from app.features.auth.application.dtos import (
    LoginInputDTO,
    LoginOutputDTO,
    RefreshTokenInputDTO,
    RegisterClientInputDTO,
    TokenPairOutputDTO,
    UserOutputDTO,
)
from app.features.auth.domain.entities import RefreshToken, User
from app.features.auth.domain.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
    TokenExpiredOrRevokedError,
    UserAlreadyExistsError,
)
from app.features.auth.domain.protocols import (
    PasswordHasherProtocol,
    RefreshTokenRepositoryProtocol,
    TokenServiceProtocol,
    UserRepositoryProtocol,
)
from app.features.auth.infrastructure.token_service import JwtTokenService


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
    """Use case to authenticate user credentials, persist refresh token, and issue tokens."""

    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        hasher: PasswordHasherProtocol,
        token_service: TokenServiceProtocol,
        refresh_token_repo: RefreshTokenRepositoryProtocol | None = None,
    ):
        self._user_repo = user_repo
        self._hasher = hasher
        self._token_service = token_service
        self._refresh_token_repo = refresh_token_repo

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

        # Persist refresh token if repository is provided
        if self._refresh_token_repo:
            payload = self._token_service.decode_token(refresh_token)
            expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            token_hash = JwtTokenService.hash_token(refresh_token)
            await self._refresh_token_repo.create(
                RefreshToken(
                    id=None,
                    user_id=user.id,
                    token_hash=token_hash,
                    expires_at=expires_at,
                    is_revoked=False,
                )
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


class RefreshTokenUseCase:
    """Use case to rotate and issue new access & refresh tokens."""

    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        refresh_token_repo: RefreshTokenRepositoryProtocol,
        token_service: TokenServiceProtocol,
    ):
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._token_service = token_service

    async def execute(self, dto: RefreshTokenInputDTO) -> TokenPairOutputDTO:
        payload = self._token_service.decode_token(dto.refresh_token)
        if payload.get("type") != "refresh":
            raise TokenExpiredOrRevokedError("Invalid token type. Refresh token required.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise TokenExpiredOrRevokedError("Invalid token claims.")

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError) as e:
            raise TokenExpiredOrRevokedError("Invalid token subject.") from e

        token_hash = JwtTokenService.hash_token(dto.refresh_token)
        persisted_token = await self._refresh_token_repo.get_by_hash(token_hash)
        if not persisted_token or persisted_token.is_revoked:
            # If revoked token was attempted, revoke all tokens for this user for security
            if persisted_token and persisted_token.is_revoked:
                await self._refresh_token_repo.revoke_all_for_user(user_id)
            raise TokenExpiredOrRevokedError("Refresh token is expired or revoked.")

        now = datetime.now(timezone.utc)
        if persisted_token.expires_at.tzinfo is None:
            expires_at = persisted_token.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = persisted_token.expires_at

        if expires_at < now:
            await self._refresh_token_repo.revoke(token_hash)
            raise TokenExpiredOrRevokedError("Refresh token has expired.")

        # Revoke the used refresh token (rotation)
        await self._refresh_token_repo.revoke(token_hash)

        # Verify user is still active
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise TokenExpiredOrRevokedError("User not found.")
        if not user.is_active:
            raise AccountDisabledError()

        # Issue new pair
        new_access_token = self._token_service.create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )
        new_refresh_token = self._token_service.create_refresh_token(
            subject=str(user.id),
        )

        new_payload = self._token_service.decode_token(new_refresh_token)
        new_expires_at = datetime.fromtimestamp(new_payload["exp"], tz=timezone.utc)
        new_token_hash = JwtTokenService.hash_token(new_refresh_token)

        await self._refresh_token_repo.create(
            RefreshToken(
                id=None,
                user_id=user.id,
                token_hash=new_token_hash,
                expires_at=new_expires_at,
                is_revoked=False,
            )
        )

        return TokenPairOutputDTO(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
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


