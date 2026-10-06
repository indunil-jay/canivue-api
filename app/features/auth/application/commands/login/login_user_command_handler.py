from datetime import datetime, timezone

from app.features.auth.application.commands.login.login_user_command import (
    LoginUserCommand,
)
from app.features.auth.application.dtos.login_result_dto import LoginResultDTO
from app.features.auth.application.event_handlers.user_logged_in_event_handler import (
    UserLoggedInEventHandler,
)
from app.features.auth.application.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
)
from app.features.auth.application.interfaces.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.features.auth.application.interfaces.repositories.user_repository import (
    UserRepository,
)
from app.features.auth.application.interfaces.services.password_hasher import (
    PasswordHasher,
)
from app.features.auth.application.interfaces.services.token_service import (
    TokenService,
)
from app.features.auth.application.mappers.user_dto_mapper import UserDTOMapper
from app.features.auth.domain.entities.refresh_token import RefreshToken
from app.features.auth.domain.events.user_logged_in import (
    UserLoggedInDomainEvent,
)
from app.features.auth.infrastructure.services.token_service import JwtTokenService


class LoginUserCommandHandler:
    def __init__(
        self,
        user_repo: UserRepository,
        hasher: PasswordHasher,
        token_service: TokenService,
        refresh_token_repo: RefreshTokenRepository | None = None,
        event_handler: UserLoggedInEventHandler | None = None,
    ):
        self._user_repo = user_repo
        self._hasher = hasher
        self._token_service = token_service
        self._refresh_token_repo = refresh_token_repo
        self._event_handler = event_handler or UserLoggedInEventHandler()

    async def handle(self, command: LoginUserCommand) -> LoginResultDTO:
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

        event = UserLoggedInDomainEvent(
            user_id=user.id,
            email=user.email,
        )
        await self._event_handler.handle(event)

        return LoginResultDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserDTOMapper.to_output_dto(user),
        )
