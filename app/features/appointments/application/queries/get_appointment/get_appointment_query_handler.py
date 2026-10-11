from app.features.appointments.application.queries.get_appointment.get_appointment_query import (
    GetAppointmentQuery,
)
from app.features.appointments.application.services.appointment_participation import (
    AppointmentParticipation,
)
from app.features.appointments.domain.entities.appointment import Appointment


class GetAppointmentQueryHandler:
    def __init__(self, participation: AppointmentParticipation):
        self._participation = participation

    async def handle(self, query: GetAppointmentQuery) -> Appointment:
        return await self._participation.load(query.actor, query.appointment_id)
