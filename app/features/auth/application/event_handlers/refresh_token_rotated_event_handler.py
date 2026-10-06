import logging

from app.features.auth.domain.events.refresh_token_rotated import (
    RefreshTokenRotatedDomainEvent,
)

logger = logging.getLogger(__name__)


class RefreshTokenRotatedEventHandler:
    async def handle(self, event: RefreshTokenRotatedDomainEvent) -> None:
        logger.info(f"Refresh token rotated domain event received for user_id={event.user_id}")
