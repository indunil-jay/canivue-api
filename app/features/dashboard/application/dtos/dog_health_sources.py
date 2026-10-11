from dataclasses import dataclass
from datetime import datetime

from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.devices.application.interfaces.repositories.smart_collar_repository import (
    SmartCollarRepositoryProtocol,
)
from app.features.health_metrics.application.interfaces.repositories.metric_reading_repository import (
    MetricReadingRepositoryProtocol,
)
from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.domain.enums.metric_time_range import MetricTimeRange
from app.features.health_metrics.domain.services.build_series import build_series
from app.features.health_metrics.domain.services.history_start import history_start
from app.features.health_metrics.domain.value_objects.metric_series import MetricSeries
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.preventive_care.application.interfaces.repositories.care_task_repository import (
    CareTaskRepositoryProtocol,
)
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)


@dataclass
class DogHealthSources:
    """Everything the read models below draw on, so each takes one collaborator."""

    readings: MetricReadingRepositoryProtocol
    predictions: PredictionRepositoryProtocol
    care_tasks: CareTaskRepositoryProtocol
    appointments: AppointmentRepositoryProtocol
    collars: SmartCollarRepositoryProtocol
    records: MedicalRecordRepositoryProtocol
    vets: VetProfileRepositoryProtocol

    async def weekly(self, dog_id: str, metric: HealthMetric, now: datetime) -> MetricSeries:
        since = history_start(MetricTimeRange.WEEKLY, now)
        readings = await self.readings.list_since(dog_id, metric, since)
        return build_series(metric, MetricTimeRange.WEEKLY, readings, now)
