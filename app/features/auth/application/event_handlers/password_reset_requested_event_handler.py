import logging

from app.features.auth.domain.events.password_reset_requested import (
    PasswordResetRequestedDomainEvent,
)

logger = logging.getLogger("canivue.auth.events")


class PasswordResetRequestedEventHandler:
    async def handle(self, event: PasswordResetRequestedDomainEvent) -> None:
        logger.info(
            "User %s requested password reset token at %s",
            event.user_id,
            event.occurred_at,
        )
