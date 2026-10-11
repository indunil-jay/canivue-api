from dataclasses import dataclass, field
from datetime import datetime

from app.features.appointments.domain.constants import OWNER_ALLOWED
from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.appointments.domain.exceptions import InvalidAppointmentTransitionError
from app.features.veterinarians.domain.enums.consultation_type import ConsultationType
from app.shared.entity import BaseEntity, _utc_now

# What each status may move to. Completed, cancelled and no-show are terminal.
_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.REQUESTED: {AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED},
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.IN_PROGRESS,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.NO_SHOW,
        AppointmentStatus.CANCELLED,
    },
    AppointmentStatus.UPCOMING: {
        AppointmentStatus.IN_PROGRESS,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.NO_SHOW,
        AppointmentStatus.CANCELLED,
    },
    AppointmentStatus.IN_PROGRESS: {AppointmentStatus.COMPLETED},
}


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
    status: AppointmentStatus = AppointmentStatus.REQUESTED
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
