from app.features.appointments.application.dtos.appointment_output_dto import AppointmentOutputDTO
from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.application.mappers.appointment_dto_mapper import (
    AppointmentDTOMapper,
)
from app.features.appointments.application.queries.list_my_appointments.list_my_appointments_query import (
    ListMyAppointmentsQuery,
)


class ListMyAppointmentsQueryHandler:
    def __init__(self, appointments: AppointmentRepositoryProtocol):
        self._appointments = appointments

    async def handle(self, query: ListMyAppointmentsQuery) -> list[AppointmentOutputDTO]:
        if query.actor.is_vet:
            mine = await self._appointments.list_for_vet_user(query.actor.id)
        else:
            mine = await self._appointments.list_for_owner(query.actor.id)
        return [
            AppointmentDTOMapper.to_output_dto(item)
            for item in [a for a in mine if query.status is None or a.status == query.status]
        ]
