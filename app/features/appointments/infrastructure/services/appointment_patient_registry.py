from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.appointments.infrastructure.persistence.models.appointment_model import (
    AppointmentModel,
)
from app.features.appointments.infrastructure.persistence.repositories.appointment_repository import (
    SqlAlchemyAppointmentRepository,
)
from app.features.dogs.application.interfaces.services.patient_registry import (
    PatientRegistryProtocol,
)
from app.features.dogs.domain.entities.dog import Dog


class AppointmentPatientRegistry(SqlAlchemyAppointmentRepository, PatientRegistryProtocol):
    """A Dog is a veterinarian's patient once it has a live appointment with them."""

    async def is_patient(self, vet_user_id: int, dog: Dog) -> bool:
        linked = await self.count(
            AppointmentModel.vet_user_id == vet_user_id,
            AppointmentModel.dog_id == dog.id,
            AppointmentModel.status != AppointmentStatus.CANCELLED.value,
        )
        return linked > 0
