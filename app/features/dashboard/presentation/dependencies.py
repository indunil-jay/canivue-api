from fastapi import Depends

from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.presentation.dependencies import get_appointment_repository
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.presentation.dependencies import get_prediction_repository
from app.features.dashboard.application.dtos.dog_health_sources import DogHealthSources
from app.features.dashboard.application.interfaces.services.insight_engine import (
    InsightEngineProtocol,
)
from app.features.dashboard.application.queries.get_dashboard_summary.get_dashboard_summary_query_handler import (
    GetDashboardSummaryQueryHandler,
)
from app.features.dashboard.application.queries.get_health_insights.get_health_insights_query_handler import (
    GetHealthInsightsQueryHandler,
)
from app.features.dashboard.application.queries.get_health_timeline.get_health_timeline_query_handler import (
    GetHealthTimelineQueryHandler,
)
from app.features.dashboard.infrastructure.ml.engine import StubInsightEngine
from app.features.devices.application.interfaces.repositories.smart_collar_repository import (
    SmartCollarRepositoryProtocol,
)
from app.features.devices.presentation.dependencies import get_collar_repository
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.health_metrics.application.interfaces.repositories.metric_reading_repository import (
    MetricReadingRepositoryProtocol,
)
from app.features.health_metrics.presentation.dependencies import get_metric_reading_repository
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.medical_records.presentation.dependencies import get_record_repository
from app.features.preventive_care.application.interfaces.repositories.care_task_repository import (
    CareTaskRepositoryProtocol,
)
from app.features.preventive_care.presentation.dependencies import get_care_task_repository
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.presentation.dependencies import get_vet_profile_repository

_insight_engine = StubInsightEngine()


def get_insight_engine() -> InsightEngineProtocol:
    return _insight_engine


def get_dog_health_sources(
    readings: MetricReadingRepositoryProtocol = Depends(get_metric_reading_repository),
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    care_tasks: CareTaskRepositoryProtocol = Depends(get_care_task_repository),
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
    collars: SmartCollarRepositoryProtocol = Depends(get_collar_repository),
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    vets: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
) -> DogHealthSources:
    return DogHealthSources(readings, predictions, care_tasks, appointments, collars, records, vets)


def get_dashboard_summary_query_handler(
    sources: DogHealthSources = Depends(get_dog_health_sources),
    access: DogAccess = Depends(get_dog_access),
) -> GetDashboardSummaryQueryHandler:
    return GetDashboardSummaryQueryHandler(sources, access)


def get_health_timeline_query_handler(
    sources: DogHealthSources = Depends(get_dog_health_sources),
    access: DogAccess = Depends(get_dog_access),
) -> GetHealthTimelineQueryHandler:
    return GetHealthTimelineQueryHandler(sources, access)


def get_health_insights_query_handler(
    sources: DogHealthSources = Depends(get_dog_health_sources),
    access: DogAccess = Depends(get_dog_access),
    engine: InsightEngineProtocol = Depends(get_insight_engine),
) -> GetHealthInsightsQueryHandler:
    return GetHealthInsightsQueryHandler(sources, access, engine)
