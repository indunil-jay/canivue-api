from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class GetAppointmentQuery:
    actor: Actor
    appointment_id: str
