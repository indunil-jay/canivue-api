from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.domain.entities.appointment import Appointment
from app.features.appointments.domain.exceptions import AppointmentNotFoundError
from app.shared.actor import Actor


class AppointmentParticipation:
    def __init__(self, appointments: AppointmentRepositoryProtocol):
        self._appointments = appointments

    async def load(self, actor: Actor, appointment_id: str) -> Appointment:
        appointment = await self._appointments.get_by_id(appointment_id)
        if appointment is None or not (
            actor.is_admin or actor.id in (appointment.owner_id, appointment.vet_user_id)
        ):
            raise AppointmentNotFoundError()
        return appointment
