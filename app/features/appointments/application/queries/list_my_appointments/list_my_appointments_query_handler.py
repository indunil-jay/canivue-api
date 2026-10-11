from collections.abc import Sequence

from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.application.queries.list_my_appointments.list_my_appointments_query import (
    ListMyAppointmentsQuery,
)
from app.features.appointments.domain.entities.appointment import Appointment


class ListMyAppointmentsQueryHandler:
    def __init__(self, appointments: AppointmentRepositoryProtocol):
        self._appointments = appointments

    async def handle(self, query: ListMyAppointmentsQuery) -> Sequence[Appointment]:
        if query.actor.is_vet:
            mine = await self._appointments.list_for_vet_user(query.actor.id)
        else:
            mine = await self._appointments.list_for_owner(query.actor.id)
        return [a for a in mine if query.status is None or a.status == query.status]
