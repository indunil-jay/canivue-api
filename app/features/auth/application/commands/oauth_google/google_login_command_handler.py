from datetime import datetime, timezone

from app.features.auth.application.commands.oauth_google.google_login_command import (
    GoogleLoginCommand,
)
from app.features.auth.application.dtos.login_result_dto import LoginResultDTO
from app.features.auth.application.event_handlers.google_user_authenticated_event_handler import (
    GoogleUserAuthenticatedEventHandler,
)
from app.features.auth.application.exceptions import (
    AccountDisabledError,
    GoogleAuthFailedError,
)
from app.features.auth.application.interfaces.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.features.auth.application.interfaces.repositories.user_repository import (
    UserRepository,
)
from app.features.auth.application.interfaces.services.google_auth_service import (
    GoogleAuthService,
)
from app.features.auth.application.interfaces.services.token_service import (
    TokenService,
)
from app.features.auth.application.mappers.user_dto_mapper import UserDTOMapper
from app.features.auth.domain.entities.refresh_token import RefreshToken
from app.features.auth.domain.entities.user import User
from app.features.auth.domain.enums.role import Role
from app.features.auth.domain.events.google_user_authenticated import (
    GoogleUserAuthenticatedDomainEvent,
)
from app.features.auth.infrastructure.services.token_service import JwtTokenService


class GoogleLoginCommandHandler:
    def __init__(
        self,
        user_repo: UserRepository,
        google_service: GoogleAuthService,
        token_service: TokenService,
        refresh_token_repo: RefreshTokenRepository | None = None,
        event_handler: GoogleUserAuthenticatedEventHandler | None = None,
    ):
        self._user_repo = user_repo
        self._google_service = google_service
        self._token_service = token_service
        self._refresh_token_repo = refresh_token_repo
        self._event_handler = event_handler or GoogleUserAuthenticatedEventHandler()

    async def handle(self, command: GoogleLoginCommand) -> LoginResultDTO:
        profile = await self._google_service.verify_id_token(command.id_token)
        if not profile.email_verified:
            raise GoogleAuthFailedError("Google account email is not verified.")

        normalized_email = profile.email.strip().lower()
        now = datetime.now(timezone.utc)
        is_new_user = False

        user = await self._user_repo.get_by_google_id(profile.google_id)
        if not user:
            user = await self._user_repo.get_by_email(normalized_email)
            if user:
                user.google_id = profile.google_id
                if profile.full_name and not user.full_name:
                    user.full_name = profile.full_name
                user.updated_at = now
                user = await self._user_repo.update(user)
            else:
                is_new_user = True
                new_user = User(
                    id=None,
                    email=normalized_email,
                    hashed_password=None,
                    role=Role.CLIENT,
                    full_name=profile.full_name,
                    google_id=profile.google_id,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                user = await self._user_repo.create(new_user)

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

        event = GoogleUserAuthenticatedDomainEvent(
            user_id=user.id,
            email=user.email,
            is_new_user=is_new_user,
            occurred_at=now,
        )
        await self._event_handler.handle(event)

        return LoginResultDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserDTOMapper.to_output_dto(user),
        )
