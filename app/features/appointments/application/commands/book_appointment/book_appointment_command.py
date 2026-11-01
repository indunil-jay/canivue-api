from dataclasses import dataclass

from app.features.appointments.application.dtos.book_appointment_input import BookAppointmentInput
from app.shared.actor import Actor


@dataclass(frozen=True)
class BookAppointmentCommand:
    actor: Actor
    data: BookAppointmentInput
