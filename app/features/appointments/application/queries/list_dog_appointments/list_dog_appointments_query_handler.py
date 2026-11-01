from app.features.appointments.application.dtos.appointment_output_dto import AppointmentOutputDTO
from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.application.mappers.appointment_dto_mapper import (
    AppointmentDTOMapper,
)
from app.features.appointments.application.queries.list_dog_appointments.list_dog_appointments_query import (
    ListDogAppointmentsQuery,
)
from app.features.dogs.application.services.dog_access import DogAccess


class ListDogAppointmentsQueryHandler:
    def __init__(self, appointments: AppointmentRepositoryProtocol, access: DogAccess):
        self._appointments = appointments
        self._access = access

    async def handle(self, query: ListDogAppointmentsQuery) -> list[AppointmentOutputDTO]:
        dog = await self._access.readable(query.actor, query.dog_id)
        appointments = await self._appointments.list_for_dog(dog.id)
        if query.actor.is_vet and dog.owner_id != query.actor.id:
            # A treating veterinarian sees their own appointments, not the Dog's other vets'.
            return [
                AppointmentDTOMapper.to_output_dto(item)
                for item in [a for a in appointments if a.vet_user_id == query.actor.id]
            ]
        return [AppointmentDTOMapper.to_output_dto(item) for item in appointments]
