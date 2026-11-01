from datetime import datetime, time, timezone
from itertools import pairwise

from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.dashboard.application.dtos.dog_health_sources import DogHealthSources
from app.features.dashboard.application.queries.get_health_timeline.get_health_timeline_query import (
    GetHealthTimelineQuery,
)
from app.features.dashboard.application.services.helpers import ELEVATED_STATUSES, VITALS
from app.features.dashboard.domain.enums.timeline_event_type import TimelineEventType
from app.features.dashboard.domain.value_objects.health_timeline_event import HealthTimelineEvent
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.domain.enums.metric_time_range import MetricTimeRange
from app.features.health_metrics.domain.services.history_start import history_start
from app.features.medical_records.domain.enums.medical_record_type import MedicalRecordType
from app.features.preventive_care.domain.enums.care_task_category import CareTaskCategory

WEIGHT_CHANGE_KG = 0.5


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


class GetHealthTimelineQueryHandler:
    """One chronological view assembled from the modules that own each kind of event."""

    def __init__(self, sources: DogHealthSources, access: DogAccess):
        self._s = sources
        self._access = access

    async def handle(self, query: GetHealthTimelineQuery) -> list[HealthTimelineEvent]:
        dog = await self._access.readable(query.actor, query.dog_id)
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
            kind = T.HEALTH_ALERT if p.status in ELEVATED_STATUSES else T.AI_PREDICTION
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
