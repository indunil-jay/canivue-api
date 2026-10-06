import hashlib
from datetime import datetime, timezone

from app.features.auth.application.commands.reset_password.reset_password_command import (
    ResetPasswordCommand,
)
from app.features.auth.application.event_handlers.password_reset_completed_event_handler import (
    PasswordResetCompletedEventHandler,
)
from app.features.auth.application.exceptions import (
    InvalidResetTokenError,
    ResetTokenExpiredError,
)
from app.features.auth.application.interfaces.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
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
from app.features.auth.domain.events.password_reset_completed import (
    PasswordResetCompletedDomainEvent,
)
from app.features.auth.domain.exceptions import (
    UserNotFoundError,
    WeakPasswordError,
)


class ResetPasswordCommandHandler:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: PasswordResetTokenRepository,
        refresh_token_repo: RefreshTokenRepository,
        hasher: PasswordHasher,
        event_handler: PasswordResetCompletedEventHandler | None = None,
    ):
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._refresh_token_repo = refresh_token_repo
        self._hasher = hasher
        self._event_handler = event_handler or PasswordResetCompletedEventHandler()

    async def handle(self, command: ResetPasswordCommand) -> bool:
        if len(command.new_password) < 8:
            raise WeakPasswordError()

        token_hash = hashlib.sha256(command.token.encode("utf-8")).hexdigest()
        token_record = await self._token_repo.get_by_hash(token_hash)
        if not token_record or token_record.is_used:
            raise InvalidResetTokenError()

        now = datetime.now(timezone.utc)
        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            await self._token_repo.mark_as_used(token_hash)
            raise ResetTokenExpiredError()

        user = await self._user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise UserNotFoundError()

        user.hashed_password = self._hasher.hash(command.new_password)
        user.updated_at = now
        await self._user_repo.update(user)

        await self._token_repo.mark_as_used(token_hash)
        await self._refresh_token_repo.revoke_all_for_user(user.id)

        event = PasswordResetCompletedDomainEvent(
            user_id=user.id,
            occurred_at=now,
        )
        await self._event_handler.handle(event)

        return True
