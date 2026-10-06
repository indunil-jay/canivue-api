import logging

from app.features.auth.application.commands.create_client.events import ClientCreatedEvent

logger = logging.getLogger(__name__)


class ClientCreatedEventHandler:
    """Handles events emitted after client account creation (e.g. welcome emails, audit logging)."""

    async def handle(self, event: ClientCreatedEvent) -> None:
        logger.info(
            f"Client account created event received for user_id={event.user_id}, email={event.email}"
        )
