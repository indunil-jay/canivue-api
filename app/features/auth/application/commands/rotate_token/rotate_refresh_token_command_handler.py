from datetime import datetime, timezone

from app.features.auth.application.commands.rotate_token.rotate_refresh_token_command import (
    RotateRefreshTokenCommand,
)
from app.features.auth.application.dtos.token_pair_output_dto import (
    TokenPairOutputDTO,
)
from app.features.auth.application.event_handlers.refresh_token_rotated_event_handler import (
    RefreshTokenRotatedEventHandler,
)
from app.features.auth.application.exceptions import (
    AccountDisabledError,
    TokenExpiredOrRevokedError,
)
from app.features.auth.application.interfaces.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.features.auth.application.interfaces.repositories.user_repository import (
    UserRepository,
)
from app.features.auth.application.interfaces.services.token_service import (
    TokenService,
)
from app.features.auth.domain.entities.refresh_token import RefreshToken
from app.features.auth.domain.events.refresh_token_rotated import (
    RefreshTokenRotatedDomainEvent,
)
from app.features.auth.infrastructure.services.token_service import JwtTokenService


class RotateRefreshTokenCommandHandler:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        token_service: TokenService,
        event_handler: RefreshTokenRotatedEventHandler | None = None,
    ):
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._token_service = token_service
        self._event_handler = event_handler or RefreshTokenRotatedEventHandler()

    async def handle(self, command: RotateRefreshTokenCommand) -> TokenPairOutputDTO:
        payload = self._token_service.decode_token(command.refresh_token)
        if payload.get("type") != "refresh":
            raise TokenExpiredOrRevokedError("Invalid token type. Refresh token required.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise TokenExpiredOrRevokedError("Invalid token claims.")

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError) as e:
            raise TokenExpiredOrRevokedError("Invalid token subject.") from e

        token_hash = JwtTokenService.hash_token(command.refresh_token)
        persisted_token = await self._refresh_token_repo.get_by_hash(token_hash)
        if not persisted_token or persisted_token.is_revoked:
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

        await self._refresh_token_repo.revoke(token_hash)

        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise TokenExpiredOrRevokedError("User not found.")
        if not user.is_active:
            raise AccountDisabledError()

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

        event = RefreshTokenRotatedDomainEvent(user_id=user.id, occurred_at=now)
        await self._event_handler.handle(event)

        return TokenPairOutputDTO(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )
