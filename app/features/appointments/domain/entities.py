from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.features.appointments.domain.exceptions import InvalidAppointmentTransitionError
from app.features.veterinarians.domain.entities import ConsultationType
from app.shared.entity import BaseEntity, _utc_now


class AppointmentStatus(str, Enum):
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    UPCOMING = "upcoming"
    IN_PROGRESS = "inProgress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "noShow"


S = AppointmentStatus

# What each status may move to. Completed, cancelled and no-show are terminal.
_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    S.REQUESTED: {S.CONFIRMED, S.CANCELLED},
    S.CONFIRMED: {S.IN_PROGRESS, S.COMPLETED, S.NO_SHOW, S.CANCELLED},
    S.UPCOMING: {S.IN_PROGRESS, S.COMPLETED, S.NO_SHOW, S.CANCELLED},
    S.IN_PROGRESS: {S.COMPLETED},
}
OWNER_ALLOWED = {S.CANCELLED}
SLOT_FREEING = {S.CANCELLED, S.NO_SHOW}


@dataclass
class Appointment(BaseEntity):
    owner_id: int = 0
    owner_name: str = ""
    vet_id: str = ""
    vet_user_id: int = 0
    vet_name: str = ""
    dog_id: str = ""
    dog_name: str = ""
    date_time: datetime = field(default_factory=_utc_now)
    status: AppointmentStatus = S.REQUESTED
    consultation_type: ConsultationType = ConsultationType.VIDEO
    fee_usd: float = 0.0
    notes: str = ""

    def move_to(self, target: AppointmentStatus, by_veterinarian: bool) -> None:
        if target not in _TRANSITIONS.get(self.status, set()):
            raise InvalidAppointmentTransitionError(self.status.value, target.value)
        if not by_veterinarian and target not in OWNER_ALLOWED:
            raise InvalidAppointmentTransitionError(self.status.value, target.value)
        self.status = target
        self.updated_at = _utc_now()
