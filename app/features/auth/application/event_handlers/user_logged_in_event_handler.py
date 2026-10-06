import logging

from app.features.auth.domain.events.user_logged_in import (
    UserLoggedInDomainEvent,
)

logger = logging.getLogger(__name__)


class UserLoggedInEventHandler:
    async def handle(self, event: UserLoggedInDomainEvent) -> None:
        logger.info(
            f"User logged in domain event received for user_id={event.user_id}, email={event.email}"
        )
