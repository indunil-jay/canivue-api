from enum import Enum


class AppointmentStatus(str, Enum):
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    UPCOMING = "upcoming"
    IN_PROGRESS = "inProgress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "noShow"
