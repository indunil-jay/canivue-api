from dataclasses import dataclass

from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.shared.actor import Actor


@dataclass(frozen=True)
class ChangeAppointmentStatusCommand:
    actor: Actor
    appointment_id: str
    target: AppointmentStatus
