from collections.abc import Sequence
from datetime import datetime

from app.core.dataclass_repository import DataclassRepository
from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.domain.constants import SLOT_FREEING
from app.features.appointments.domain.entities.appointment import Appointment
from app.features.appointments.infrastructure.persistence.models.appointment_model import (
    AppointmentModel,
)

_FREED = [s.value for s in SLOT_FREEING]


class SqlAlchemyAppointmentRepository(
    DataclassRepository[Appointment, AppointmentModel], AppointmentRepositoryProtocol
):
    _model_cls = AppointmentModel
    _entity_cls = Appointment

    async def list_for_dog(self, dog_id: str) -> Sequence[Appointment]:
        return await self.find(
            AppointmentModel.dog_id == dog_id, order_by=AppointmentModel.date_time
        )

    async def list_for_owner(self, owner_id: int) -> Sequence[Appointment]:
        return await self.find(
            AppointmentModel.owner_id == owner_id, order_by=AppointmentModel.date_time
        )

    async def list_for_vet_user(self, vet_user_id: int) -> Sequence[Appointment]:
        return await self.find(
            AppointmentModel.vet_user_id == vet_user_id, order_by=AppointmentModel.date_time
        )

    async def slot_is_taken(self, vet_id: str, date_time: datetime) -> bool:
        taken = await self.count(
            AppointmentModel.vet_id == vet_id,
            AppointmentModel.date_time == date_time,
            AppointmentModel.status.not_in(_FREED),
        )
        return taken > 0
