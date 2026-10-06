import logging

from app.features.auth.domain.events.staff_user_created import (
    StaffUserCreatedDomainEvent,
)

logger = logging.getLogger(__name__)


class StaffUserCreatedEventHandler:
    async def handle(self, event: StaffUserCreatedDomainEvent) -> None:
        logger.info(
            f"Staff user created domain event received for user_id={event.user_id}, "
            f"email={event.email}, role={event.role.value}"
        )
