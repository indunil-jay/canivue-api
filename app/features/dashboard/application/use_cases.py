from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from itertools import pairwise

from app.features.appointments.domain.entities import AppointmentStatus
from app.features.appointments.domain.repositories import AppointmentRepositoryProtocol
from app.features.assessments.domain.entities import (
    Prediction,
    PredictionRepositoryProtocol,
    PredictionStatus,
)
from app.features.dashboard.domain.entities import (
    ACTIVITY_GOAL_STEPS,
    HYDRATION_ML_PER_KG,
    AiInsight,
    CareReminder,
    DashboardSummary,
    DeviceConnectionState,
    DeviceStatus,
    HealthInsight,
    HealthTimelineEvent,
    InsightEngineProtocol,
    InsightRisk,
    MetricTrend,
    ReminderKind,
    TimelineEventType,
    UpcomingAppointment,
    VitalsSnapshot,
    health_score,
)
from app.features.devices.domain.entities import (
    CollarConnectionState,
    SmartCollar,
    SmartCollarRepositoryProtocol,
)
from app.features.dogs.application.access import DogAccess
from app.features.dogs.domain.entities import Dog
from app.features.health_metrics.domain.entities import (
    CUMULATIVE,
    HealthMetric,
    MetricReadingRepositoryProtocol,
    MetricSeries,
    MetricTimeRange,
    build_series,
    history_start,
)
from app.features.medical_records.domain.entities import (
    MedicalRecordRepositoryProtocol,
    MedicalRecordType,
)
from app.features.preventive_care.domain.entities import (
    CareTaskCategory,
    CareTaskRepositoryProtocol,
)
from app.features.veterinarians.domain.entities import ConsultationType
from app.features.veterinarians.domain.repositories import VetProfileRepositoryProtocol
from app.shared.actor import Actor

REMINDER_LIMIT = 3
WEIGHT_CHANGE_KG = 0.5
VITALS = (
    HealthMetric.HEART_RATE,
    HealthMetric.TEMPERATURE,
    HealthMetric.ACTIVITY,
    HealthMetric.SLEEP,
)

_REMINDER_KINDS = {
    CareTaskCategory.VACCINATION: ReminderKind.VACCINATION,
    CareTaskCategory.MEDICATION: ReminderKind.MEDICATION,
    CareTaskCategory.GROOMING: ReminderKind.GROOMING,
    CareTaskCategory.DEWORMING: ReminderKind.DEWORMING,
}
_ELEVATED = {PredictionStatus.HIGH_RISK, PredictionStatus.VET_REVIEW_RECOMMENDED}
_RECORD_EVENTS = {
    MedicalRecordType.DIAGNOSIS: TimelineEventType.DIAGNOSIS,
    MedicalRecordType.LAB_RESULT: TimelineEventType.DIAGNOSIS,
    MedicalRecordType.PRESCRIPTION: TimelineEventType.MEDICATION,
}
_METRIC_LABELS = {
    HealthMetric.HEART_RATE: ("Heart rate", "bpm"),
    HealthMetric.TEMPERATURE: ("Temperature", "°C"),
    HealthMetric.ACTIVITY: ("Activity", "steps"),
    HealthMetric.SLEEP: ("Sleep", "hrs"),
}


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


def _insight(dog: Dog, prediction: Prediction | None) -> AiInsight:
    if prediction is None:
        return AiInsight(
            headline="No concerns on record",
            detail=f"Run a health check to get an AI read on how {dog.name} is doing.",
        )
    if prediction.status in _ELEVATED:
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


class GetDashboardSummaryUseCase:
    def __init__(self, sources: DogHealthSources, access: DogAccess):
        self._s = sources
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> DashboardSummary:
        dog = await self._access.readable(actor, dog_id)
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


class GetHealthTimelineUseCase:
    """One chronological view assembled from the modules that own each kind of event."""

    def __init__(self, sources: DogHealthSources, access: DogAccess):
        self._s = sources
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> list[HealthTimelineEvent]:
        dog = await self._access.readable(actor, dog_id)
        now = datetime.now(timezone.utc)
        E, T = HealthTimelineEvent, TimelineEventType
        events: list[HealthTimelineEvent] = []

        for v in dog.vaccinations:
            given = datetime.combine(v.date_given, time(12), tzinfo=timezone.utc)
            due = f" Next due {v.next_due_date:%d %b %Y}." if v.next_due_date else ""
            events.append(E(T.VACCINATION, f"{v.name} vaccination", f"Vaccine given.{due}", given))

        for task in await self._s.care_tasks.list_for_dog(dog.id):
            if task.completed and task.completed_at:
                kind = (
                    T.MEDICATION if task.category == CareTaskCategory.MEDICATION else T.VACCINATION
                )
                if task.category in (CareTaskCategory.MEDICATION, CareTaskCategory.VACCINATION):
                    events.append(E(kind, task.title, "Marked done.", task.completed_at))

        for record in await self._s.records.list_for_dog(dog.id):
            if record.type in _RECORD_EVENTS:
                events.append(
                    E(_RECORD_EVENTS[record.type], record.title, record.description, record.date)
                )

        for a in await self._s.appointments.list_for_dog(dog.id):
            if a.status != AppointmentStatus.CANCELLED:
                events.append(
                    E(T.APPOINTMENT, f"Appointment with {a.vet_name}", a.status.value, a.date_time)
                )

        for p in await self._s.predictions.list_for_dog(dog.id):
            kind = T.HEALTH_ALERT if p.status in _ELEVATED else T.AI_PREDICTION
            detail = f"{p.combined_risk_percent:.0f}% risk. {p.recommended_next_step}"
            events.append(E(kind, p.title, detail, p.prediction_date))

        monthly_start = history_start(MetricTimeRange.MONTHLY, now)
        weights = await self._s.readings.list_since(dog.id, HealthMetric.WEIGHT, monthly_start)
        for before, after in pairwise(weights):
            change = after.value - before.value
            if abs(change) >= WEIGHT_CHANGE_KG:
                events.append(
                    E(
                        T.WEIGHT_CHANGE,
                        f"Weight {after.value:.1f} kg",
                        f"{change:+.1f} kg since the previous weigh-in.",
                        after.recorded_at,
                    )
                )

        for metric in VITALS:
            label, unit = _METRIC_LABELS[metric]
            series = await self._s.weekly(dog.id, metric, now)
            for point in series.points:
                if point.is_abnormal:
                    side = "above" if point.value > series.baseline_average else "below"
                    events.append(
                        E(
                            T.SENSOR_EVENT,
                            f"{label} {side} baseline",
                            f"{point.value:g} {unit} against a baseline of "
                            f"{series.baseline_average:g} {unit}.",
                            point.date,
                        )
                    )

        return sorted(events, key=lambda e: e.date, reverse=True)


class GetHealthInsightsUseCase:
    def __init__(self, sources: DogHealthSources, access: DogAccess, engine: InsightEngineProtocol):
        self._s = sources
        self._access = access
        self._engine = engine

    async def execute(self, actor: Actor, dog_id: str) -> list[HealthInsight]:
        dog = await self._access.readable(actor, dog_id)
        now = datetime.now(timezone.utc)
        boundary = now - timedelta(days=30)
        trends = []
        for metric in HealthMetric:
            readings = await self._s.readings.list_since(dog.id, metric, now - timedelta(days=60))
            recent = [r for r in readings if r.recorded_at >= boundary]
            previous = [r for r in readings if r.recorded_at < boundary]
            if recent and previous:
                trends.append(
                    MetricTrend(
                        metric, _daily_average(metric, recent), _daily_average(metric, previous)
                    )
                )
        return await self._engine.summarise(dog.name, trends)


def _daily_average(metric: HealthMetric, readings: list) -> float:
    """Average per day: cumulative metrics are totalled within a day first."""
    by_day: dict = {}
    for r in readings:
        by_day.setdefault(r.recorded_at.date(), []).append(r.value)
    combine = sum if metric in CUMULATIVE else (lambda values: sum(values) / len(values))
    daily = [combine(values) for values in by_day.values()]
    return sum(daily) / len(daily)
