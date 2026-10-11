from enum import Enum
from typing import Protocol


class NotificationType(str, Enum):
    AI_HEALTH_ALERT = "aiHealthAlert"
    VACCINE_REMINDER = "vaccineReminder"
    ACTIVITY_GOAL = "activityGoal"
    SMART_COLLAR = "smartCollar"
    VET_APPOINTMENT = "vetAppointment"
    VET_MESSAGE = "vetMessage"
    MEDICATION_REMINDER = "medicationReminder"
    COMMUNITY_ACTIVITY = "communityActivity"
    BILLING = "billing"


class NotifierProtocol(Protocol):
    """How any module tells a user that something happened."""

    async def notify(
        self,
        user_id: int,
        type: NotificationType,
        title: str,
        message: str,
        dog_name: str = "",
        action_label: str | None = None,
    ) -> None: ...
