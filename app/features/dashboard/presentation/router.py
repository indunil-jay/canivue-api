from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.core.response import APIResponse
from app.features.appointments.domain.repositories import AppointmentRepositoryProtocol
from app.features.appointments.presentation.dependencies import get_appointment_repository
from app.features.assessments.domain.entities import PredictionRepositoryProtocol
from app.features.assessments.presentation.dependencies import get_prediction_repository
from app.features.auth.presentation.dependencies import get_actor
from app.features.dashboard.application.use_cases import (
    DogHealthSources,
    GetDashboardSummaryUseCase,
    GetHealthInsightsUseCase,
    GetHealthTimelineUseCase,
)
from app.features.dashboard.domain.entities import (
    DeviceConnectionState,
    InsightEngineProtocol,
    InsightRisk,
    ReminderKind,
    TimelineEventType,
    TrendDirection,
)
from app.features.dashboard.infrastructure.ml.engine import StubInsightEngine
from app.features.devices.domain.entities import SmartCollarRepositoryProtocol
from app.features.devices.presentation.router import get_collar_repository
from app.features.dogs.application.access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.health_metrics.domain.entities import MetricReadingRepositoryProtocol
from app.features.health_metrics.presentation.router import get_metric_reading_repository
from app.features.medical_records.domain.entities import MedicalRecordRepositoryProtocol
from app.features.medical_records.presentation.router import get_record_repository
from app.features.preventive_care.domain.entities import CareTaskRepositoryProtocol
from app.features.preventive_care.presentation.router import get_care_task_repository
from app.features.veterinarians.domain.repositories import VetProfileRepositoryProtocol
from app.features.veterinarians.presentation.dependencies import get_vet_profile_repository
from app.shared.actor import Actor

router = APIRouter()

_FROM = ConfigDict(from_attributes=True)


class VitalsSnapshotSchema(BaseModel):
    model_config = _FROM

    heart_rate_bpm: int | None
    temperature_c: float | None
    activity_steps_today: int
    activity_goal_steps: int
    sleep_hours_last_night: float | None
    hydration_ml: int
    hydration_goal_ml: int
    weight_kg: float


class AiInsightSchema(BaseModel):
    model_config = _FROM

    headline: str
    detail: str
    risk: InsightRisk


class CareReminderSchema(BaseModel):
    model_config = _FROM

    kind: ReminderKind
    title: str
    due_date: datetime
    is_overdue: bool


class UpcomingAppointmentSchema(BaseModel):
    model_config = _FROM

    vet_name: str
    clinic: str
    time: datetime
    is_video_call: bool


class DeviceStatusSchema(BaseModel):
    model_config = _FROM

    state: DeviceConnectionState
    device_name: str
    battery_percent: int | None
    last_synced_at: datetime | None


class DashboardSummaryResponse(BaseModel):
    model_config = _FROM

    health_score: int | None = Field(
        ..., description="0-100, or null when the Dog has no readings and no prediction yet"
    )
    vitals: VitalsSnapshotSchema
    insight: AiInsightSchema
    reminders: list[CareReminderSchema]
    appointment: UpcomingAppointmentSchema | None
    device: DeviceStatusSchema


class HealthTimelineEventResponse(BaseModel):
    model_config = _FROM

    type: TimelineEventType
    title: str
    description: str
    date: datetime


class HealthInsightResponse(BaseModel):
    model_config = _FROM

    headline: str
    detail: str
    direction: TrendDirection
    is_positive: bool


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


def get_dashboard_summary_use_case(
    sources: DogHealthSources = Depends(get_dog_health_sources),
    access: DogAccess = Depends(get_dog_access),
) -> GetDashboardSummaryUseCase:
    return GetDashboardSummaryUseCase(sources, access)


def get_health_timeline_use_case(
    sources: DogHealthSources = Depends(get_dog_health_sources),
    access: DogAccess = Depends(get_dog_access),
) -> GetHealthTimelineUseCase:
    return GetHealthTimelineUseCase(sources, access)


def get_health_insights_use_case(
    sources: DogHealthSources = Depends(get_dog_health_sources),
    access: DogAccess = Depends(get_dog_access),
    engine: InsightEngineProtocol = Depends(get_insight_engine),
) -> GetHealthInsightsUseCase:
    return GetHealthInsightsUseCase(sources, access, engine)


@router.get(
    "/{dog_id}/dashboard",
    response_model=APIResponse[DashboardSummaryResponse],
    summary="Everything the home screen shows for one Dog",
)
async def get_dashboard(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: GetDashboardSummaryUseCase = Depends(get_dashboard_summary_use_case),
) -> APIResponse[DashboardSummaryResponse]:
    summary = await use_case.execute(actor, dog_id)
    return APIResponse(
        message="Dashboard retrieved successfully",
        data=DashboardSummaryResponse.model_validate(summary),
    )


@router.get(
    "/{dog_id}/timeline",
    response_model=APIResponse[list[HealthTimelineEventResponse]],
    summary="A Dog's unified health timeline, newest first",
)
async def get_timeline(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: GetHealthTimelineUseCase = Depends(get_health_timeline_use_case),
) -> APIResponse[list[HealthTimelineEventResponse]]:
    events = await use_case.execute(actor, dog_id)
    return APIResponse(
        message="Timeline retrieved successfully",
        data=[HealthTimelineEventResponse.model_validate(e) for e in events],
    )


@router.get(
    "/{dog_id}/insights",
    response_model=APIResponse[list[HealthInsightResponse]],
    summary="Long-term trend statements for a Dog",
    description="One statement per metric that has readings in both of the last two 30-day "
    "periods. Empty until there is that much history.",
)
async def get_insights(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: GetHealthInsightsUseCase = Depends(get_health_insights_use_case),
) -> APIResponse[list[HealthInsightResponse]]:
    insights = await use_case.execute(actor, dog_id)
    return APIResponse(
        message="Insights retrieved successfully",
        data=[HealthInsightResponse.model_validate(i) for i in insights],
    )
