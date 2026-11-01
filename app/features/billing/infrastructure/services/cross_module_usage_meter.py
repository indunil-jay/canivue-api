from datetime import datetime

from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.billing.application.interfaces.services.usage_meter import UsageMeterProtocol
from app.features.billing.domain.value_objects.usage import Usage
from app.features.devices.application.interfaces.repositories.smart_collar_repository import (
    SmartCollarRepositoryProtocol,
)
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)


class CrossModuleUsageMeter(UsageMeterProtocol):
    def __init__(
        self,
        dogs: DogRepositoryProtocol,
        predictions: PredictionRepositoryProtocol,
        collars: SmartCollarRepositoryProtocol,
        appointments: AppointmentRepositoryProtocol,
    ):
        self._dogs = dogs
        self._predictions = predictions
        self._collars = collars
        self._appointments = appointments

    async def measure(self, user_id: int, since: datetime) -> Usage:
        dog_ids = [d.id for d in await self._dogs.list_for_owner(user_id)]
        paired = 0
        for dog_id in dog_ids:
            collar = await self._collars.get_for_dog(dog_id)
            paired += bool(collar and collar.is_paired)
        consultations = [
            a
            for a in await self._appointments.list_for_owner(user_id)
            if a.status == AppointmentStatus.COMPLETED and a.date_time >= since
        ]
        return Usage(
            dogs=len(dog_ids),
            ai_analyses=await self._predictions.count_since(dog_ids, since),
            devices=paired,
            vet_consultations=len(consultations),
        )
