from datetime import datetime, timezone

from app.features.auth.application.commands.dtos import LoginCommand, LoginResultDTO
from app.features.auth.application.common_dtos import UserOutputDTO
from app.features.auth.domain.entities import RefreshToken
from app.features.auth.domain.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
)
from app.features.auth.domain.repositories import RefreshTokenRepository, UserRepository
from app.features.auth.domain.services import PasswordHasher, TokenService
from app.features.auth.infrastructure.token_service import JwtTokenService


class LoginUseCase:
    """Command Use Case to authenticate credentials, persist refresh token, and issue tokens."""

    def __init__(
        self,
        user_repo: UserRepository,
        hasher: PasswordHasher,
        token_service: TokenService,
        refresh_token_repo: RefreshTokenRepository | None = None,
    ):
        self._user_repo = user_repo
        self._hasher = hasher
        self._token_service = token_service
        self._refresh_token_repo = refresh_token_repo

    async def execute(self, command: LoginCommand) -> LoginResultDTO:
        email = command.email.strip().lower()
        user = await self._user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError()

        if not self._hasher.verify(command.password, user.hashed_password):
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
            permissions=user.permissions,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        return LoginResultDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_dto,
        )
