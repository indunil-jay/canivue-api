import logging

from app.features.auth.domain.events.password_reset_completed import (
    PasswordResetCompletedDomainEvent,
)

logger = logging.getLogger("canivue.auth.events")


class PasswordResetCompletedEventHandler:
    async def handle(self, event: PasswordResetCompletedDomainEvent) -> None:
        logger.info(
            "User %s completed password reset at %s",
            event.user_id,
            event.occurred_at,
        )
