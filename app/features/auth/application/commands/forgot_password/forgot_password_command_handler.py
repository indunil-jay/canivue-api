import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.features.auth.application.commands.forgot_password.forgot_password_command import (
    ForgotPasswordCommand,
)
from app.features.auth.application.event_handlers.password_reset_requested_event_handler import (
    PasswordResetRequestedEventHandler,
)
from app.features.auth.application.interfaces.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.features.auth.application.interfaces.repositories.user_repository import (
    UserRepository,
)
from app.features.auth.application.interfaces.services.email_service import (
    EmailService,
)
from app.features.auth.domain.entities.password_reset_token import (
    PasswordResetToken,
)
from app.features.auth.domain.events.password_reset_requested import (
    PasswordResetRequestedDomainEvent,
)


class ForgotPasswordCommandHandler:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: PasswordResetTokenRepository,
        email_service: EmailService,
        event_handler: PasswordResetRequestedEventHandler | None = None,
    ):
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._email_service = email_service
        self._event_handler = event_handler or PasswordResetRequestedEventHandler()

    async def handle(self, command: ForgotPasswordCommand) -> bool:
        normalized_email = command.email.strip().lower()
        user = await self._user_repo.get_by_email(normalized_email)
        if not user or not user.is_active:
            return True

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=15)

        await self._token_repo.invalidate_all_for_user(user.id)
        await self._token_repo.create(
            PasswordResetToken(
                id=None,
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                is_used=False,
                created_at=now,
            )
        )

        await self._email_service.send_password_reset_email(user.email, raw_token)

        event = PasswordResetRequestedDomainEvent(
            user_id=user.id,
            email=user.email,
            token=raw_token,
            occurred_at=now,
        )
        await self._event_handler.handle(event)

        return True
