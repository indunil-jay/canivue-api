import logging

from app.features.auth.domain.events.user_registered import (
    UserRegisteredDomainEvent,
)

logger = logging.getLogger(__name__)


class UserRegisteredEventHandler:
    async def handle(self, event: UserRegisteredDomainEvent) -> None:
        logger.info(
            f"User registered domain event received for user_id={event.user_id}, email={event.email}"
        )
