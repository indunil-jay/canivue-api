import logging

from app.features.auth.application.commands.create_staff.events import StaffUserCreatedEvent

logger = logging.getLogger(__name__)


class StaffUserCreatedEventHandler:
    """Handles events emitted after staff account creation (e.g. audit logs, staff provisioning notifications)."""

    async def handle(self, event: StaffUserCreatedEvent) -> None:
        logger.info(
            f"Staff account created event received for user_id={event.user_id}, "
            f"email={event.email}, role={event.role.value}"
        )
