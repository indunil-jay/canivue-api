from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class ReviewAppointmentCommand:
    actor: Actor
    appointment_id: str
    rating: int
    comment: str
