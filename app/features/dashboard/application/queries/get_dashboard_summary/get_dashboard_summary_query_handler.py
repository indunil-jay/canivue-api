from datetime import datetime, time, timedelta, timezone

from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.assessments.domain.entities.prediction import Prediction
from app.features.assessments.domain.enums.prediction_status import PredictionStatus
from app.features.dashboard.application.dtos.dog_health_sources import DogHealthSources
from app.features.dashboard.application.queries.get_dashboard_summary.get_dashboard_summary_query import (
    GetDashboardSummaryQuery,
)
from app.features.dashboard.application.services.helpers import ELEVATED_STATUSES, VITALS
from app.features.dashboard.domain.constants import ACTIVITY_GOAL_STEPS, HYDRATION_ML_PER_KG
from app.features.dashboard.domain.enums.device_connection_state import DeviceConnectionState
from app.features.dashboard.domain.enums.insight_risk import InsightRisk
from app.features.dashboard.domain.enums.reminder_kind import ReminderKind
from app.features.dashboard.domain.services.health_score import health_score
from app.features.dashboard.domain.value_objects.ai_insight import AiInsight
from app.features.dashboard.domain.value_objects.care_reminder import CareReminder
from app.features.dashboard.domain.value_objects.dashboard_summary import DashboardSummary
from app.features.dashboard.domain.value_objects.device_status import DeviceStatus
from app.features.dashboard.domain.value_objects.upcoming_appointment import UpcomingAppointment
from app.features.dashboard.domain.value_objects.vitals_snapshot import VitalsSnapshot
from app.features.devices.domain.entities.smart_collar import SmartCollar
from app.features.devices.domain.enums.collar_connection_state import CollarConnectionState
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.domain.entities.dog import Dog
from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.preventive_care.domain.enums.care_task_category import CareTaskCategory
from app.features.veterinarians.domain.enums.consultation_type import ConsultationType

REMINDER_LIMIT = 3


_REMINDER_KINDS = {
    CareTaskCategory.VACCINATION: ReminderKind.VACCINATION,
    CareTaskCategory.MEDICATION: ReminderKind.MEDICATION,
    CareTaskCategory.GROOMING: ReminderKind.GROOMING,
    CareTaskCategory.DEWORMING: ReminderKind.DEWORMING,
}


def _insight(dog: Dog, prediction: Prediction | None) -> AiInsight:
    if prediction is None:
        return AiInsight(
            headline="No concerns on record",
            detail=f"Run a health check to get an AI read on how {dog.name} is doing.",
        )
    if prediction.status in ELEVATED_STATUSES:
        risk = InsightRisk.ELEVATED
    elif prediction.status == PredictionStatus.MODERATE_RISK:
        risk = InsightRisk.MONITORING
    else:
        risk = InsightRisk.NORMAL
    return AiInsight(headline=prediction.title, detail=prediction.recommended_next_step, risk=risk)


def _device(collar: SmartCollar | None) -> DeviceStatus:
    collar = collar or SmartCollar()
    state = {
        CollarConnectionState.CONNECTED: DeviceConnectionState.CONNECTED,
        CollarConnectionState.NOT_PAIRED: DeviceConnectionState.NOT_PAIRED,
    }.get(collar.state, DeviceConnectionState.DISCONNECTED)
    return DeviceStatus(state, collar.name, collar.battery_percent, collar.last_synced_at)


class GetDashboardSummaryQueryHandler:
    def __init__(self, sources: DogHealthSources, access: DogAccess):
        self._s = sources
        self._access = access

    async def handle(self, query: GetDashboardSummaryQuery) -> DashboardSummary:
        dog = await self._access.readable(query.actor, query.dog_id)
        now = datetime.now(timezone.utc)
        today = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)

        latest = {m: await self._s.readings.latest(dog.id, m) for m in HealthMetric}
        abnormal_vitals = 0
        for metric in VITALS:
            points = (await self._s.weekly(dog.id, metric, now)).points
            abnormal_vitals += bool(points and points[-1].is_abnormal)

        async def total_since(metric: HealthMetric, since: datetime) -> float:
            return sum(r.value for r in await self._s.readings.list_since(dog.id, metric, since))

        weight = latest[HealthMetric.WEIGHT]
        weight_kg = weight.value if weight else dog.weight_kg
        heart, temperature = latest[HealthMetric.HEART_RATE], latest[HealthMetric.TEMPERATURE]
        slept = await total_since(HealthMetric.SLEEP, now - timedelta(hours=24))
        vitals = VitalsSnapshot(
            heart_rate_bpm=round(heart.value) if heart else None,
            temperature_c=round(temperature.value, 1) if temperature else None,
            activity_steps_today=round(await total_since(HealthMetric.ACTIVITY, today)),
            activity_goal_steps=ACTIVITY_GOAL_STEPS,
            sleep_hours_last_night=round(slept, 1) if latest[HealthMetric.SLEEP] else None,
            hydration_ml=round(await total_since(HealthMetric.HYDRATION, today)),
            hydration_goal_ml=round(weight_kg * HYDRATION_ML_PER_KG),
            weight_kg=round(weight_kg, 2),
        )

        prediction = await self._s.predictions.latest_active(dog.id)
        outstanding = [t for t in await self._s.care_tasks.list_for_dog(dog.id) if not t.completed]
        return DashboardSummary(
            health_score=health_score(
                prediction.combined_risk_percent if prediction else None,
                abnormal_vitals,
                has_data=prediction is not None or any(latest.values()),
            ),
            vitals=vitals,
            insight=_insight(dog, prediction),
            reminders=[
                CareReminder(
                    kind=_REMINDER_KINDS.get(t.category, ReminderKind.CHECKUP),
                    title=t.title,
                    due_date=t.due_date,
                    is_overdue=t.is_overdue,
                )
                for t in outstanding[:REMINDER_LIMIT]
            ],
            appointment=await self._next_appointment(dog.id, now),
            device=_device(await self._s.collars.get_for_dog(dog.id)),
        )

    async def _next_appointment(self, dog_id: str, now: datetime) -> UpcomingAppointment | None:
        live = {AppointmentStatus.REQUESTED, AppointmentStatus.CONFIRMED}
        upcoming = [
            a
            for a in await self._s.appointments.list_for_dog(dog_id)
            if a.status in live and a.date_time > now
        ]
        if not upcoming:
            return None
        appointment = upcoming[0]
        vet = await self._s.vets.get_by_id(appointment.vet_id)
        return UpcomingAppointment(
            vet_name=appointment.vet_name,
            clinic=vet.clinics[0] if vet and vet.clinics else "",
            time=appointment.date_time,
            is_video_call=appointment.consultation_type == ConsultationType.VIDEO,
        )
