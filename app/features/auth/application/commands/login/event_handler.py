import logging

from app.features.auth.application.commands.login.events import UserLoggedInEvent

logger = logging.getLogger(__name__)


class UserLoggedInEventHandler:
    """Handles audit logging or tracking for user logins."""

    async def handle(self, event: UserLoggedInEvent) -> None:
        logger.info(f"User login event received for user_id={event.user_id}, email={event.email}")
