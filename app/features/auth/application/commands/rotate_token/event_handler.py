import logging

from app.features.auth.application.commands.rotate_token.events import RefreshTokenRotatedEvent

logger = logging.getLogger(__name__)


class RefreshTokenRotatedEventHandler:
    """Handles audit logging or tracking for refresh token rotations."""

    async def handle(self, event: RefreshTokenRotatedEvent) -> None:
        logger.info(f"Refresh token rotated event received for user_id={event.user_id}")
