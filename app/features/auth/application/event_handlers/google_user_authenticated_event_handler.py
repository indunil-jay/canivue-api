import logging

from app.features.auth.domain.events.google_user_authenticated import (
    GoogleUserAuthenticatedDomainEvent,
)

logger = logging.getLogger("canivue.auth.events")


class GoogleUserAuthenticatedEventHandler:
    async def handle(self, event: GoogleUserAuthenticatedDomainEvent) -> None:
        logger.info(
            "Google user authenticated: id=%s email=%s new_user=%s",
            event.user_id,
            event.email,
            event.is_new_user,
        )
