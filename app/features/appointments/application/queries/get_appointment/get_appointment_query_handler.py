from app.features.appointments.application.dtos.appointment_output_dto import AppointmentOutputDTO
from app.features.appointments.application.mappers.appointment_dto_mapper import (
    AppointmentDTOMapper,
)
from app.features.appointments.application.queries.get_appointment.get_appointment_query import (
    GetAppointmentQuery,
)
from app.features.appointments.application.services.appointment_participation import (
    AppointmentParticipation,
)


class GetAppointmentQueryHandler:
    def __init__(self, participation: AppointmentParticipation):
        self._participation = participation

    async def handle(self, query: GetAppointmentQuery) -> AppointmentOutputDTO:
        return AppointmentDTOMapper.to_output_dto(
            await self._participation.load(query.actor, query.appointment_id)
        )
