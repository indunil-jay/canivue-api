from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.features.appointments.domain.entities import Appointment, AppointmentStatus
from app.features.appointments.domain.repositories import AppointmentRepositoryProtocol
from app.features.assessments.domain.entities import (
    PredictionRepositoryProtocol,
    PredictionStatus,
)
from app.features.dogs.domain.repositories import DogRepositoryProtocol
from app.features.messaging.domain.repositories import ConversationRepositoryProtocol
from app.features.veterinarians.domain.entities import ConsultationType
from app.shared.actor import Actor

NEW_PATIENT_WINDOW = timedelta(days=7)
RECENT_MESSAGE_LIMIT = 5
_CRITICAL = {PredictionStatus.HIGH_RISK, PredictionStatus.VET_REVIEW_RECOMMENDED}
_NEEDS_ATTENTION = _CRITICAL | {PredictionStatus.MODERATE_RISK}
_LIVE = {AppointmentStatus.REQUESTED, AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS}
_TYPE_LABELS = {
    ConsultationType.VIDEO: "Video Call",
    ConsultationType.IN_PERSON: "In Person",
    ConsultationType.CHAT: "Chat",
}


@dataclass(frozen=True)
class ScheduleEntry:
    appointment_id: str
    time: datetime
    owner_name: str
    dog_name: str
    type: str
    confirmed: bool


@dataclass(frozen=True)
class RecentMessagePreview:
    conversation_id: str
    owner_name: str
    preview: str
    sent_at: datetime


@dataclass(frozen=True)
class VetDashboardSummary:
    vet_name: str
    today_schedule: list[ScheduleEntry]
    waiting_consultation_count: int
    critical_alert_count: int
    new_patient_count: int
    recent_messages: list[RecentMessagePreview]


@dataclass(frozen=True)
class VetPatient:
    dog_id: str
    dog_name: str
    breed: str
    age_formatted: str
    owner_name: str
    last_visit: datetime | None
    needs_follow_up: bool
    has_critical_alert: bool
    allergies: list[str]
    existing_conditions: list[str]
    current_medications: list[str]


class VetCaseload:
    """A veterinarian's patients: the Dogs with a live or past appointment with them."""

    def __init__(
        self,
        appointments: AppointmentRepositoryProtocol,
        dogs: DogRepositoryProtocol,
        predictions: PredictionRepositoryProtocol,
    ):
        self._appointments = appointments
        self._dogs = dogs
        self._predictions = predictions

    async def appointments_of(self, actor: Actor) -> list[Appointment]:
        return [
            a
            for a in await self._appointments.list_for_vet_user(actor.id)
            if a.status != AppointmentStatus.CANCELLED
        ]

    async def patients_of(self, actor: Actor) -> list[VetPatient]:
        now = datetime.now(timezone.utc)
        by_dog: dict[str, list[Appointment]] = {}
        for appointment in await self.appointments_of(actor):
            by_dog.setdefault(appointment.dog_id, []).append(appointment)

        patients = []
        for dog in await self._dogs.list_by_ids(list(by_dog)):
            if dog.is_archived:
                continue
            visits = by_dog[dog.id]
            completed = [a.date_time for a in visits if a.status == AppointmentStatus.COMPLETED]
            has_upcoming = any(a.status in _LIVE and a.date_time > now for a in visits)
            prediction = await self._predictions.latest_active(dog.id)
            status = prediction.status if prediction else None
            patients.append(
                VetPatient(
                    dog_id=dog.id,
                    dog_name=dog.name,
                    breed=dog.breed,
                    age_formatted=dog.age_formatted,
                    owner_name=visits[0].owner_name,
                    last_visit=max(completed) if completed else None,
                    # An open concern with nothing booked to follow it up.
                    needs_follow_up=status in _NEEDS_ATTENTION and not has_upcoming,
                    has_critical_alert=status in _CRITICAL,
                    allergies=dog.allergies,
                    existing_conditions=dog.existing_conditions,
                    current_medications=[m.name for m in dog.medications],
                )
            )
        return sorted(patients, key=lambda p: (not p.has_critical_alert, p.dog_name))


class ListMyPatientsUseCase:
    def __init__(self, caseload: VetCaseload):
        self._caseload = caseload

    async def execute(self, actor: Actor) -> list[VetPatient]:
        return await self._caseload.patients_of(actor)


class GetVetDashboardUseCase:
    def __init__(self, caseload: VetCaseload, conversations: ConversationRepositoryProtocol):
        self._caseload = caseload
        self._conversations = conversations

    async def execute(self, actor: Actor) -> VetDashboardSummary:
        now = datetime.now(timezone.utc)
        appointments = await self._caseload.appointments_of(actor)
        patients = await self._caseload.patients_of(actor)

        first_seen: dict[str, datetime] = {}
        for a in appointments:
            first_seen[a.dog_id] = min(first_seen.get(a.dog_id, a.created_at), a.created_at)

        conversations = [
            c
            for c in await self._conversations.list_for_user(actor.id)
            if c.vet_user_id == actor.id and c.last_message_at
        ]
        return VetDashboardSummary(
            vet_name=actor.display_name,
            today_schedule=[
                ScheduleEntry(
                    appointment_id=a.id,
                    time=a.date_time,
                    owner_name=a.owner_name,
                    dog_name=a.dog_name,
                    type=_TYPE_LABELS[a.consultation_type],
                    confirmed=a.status != AppointmentStatus.REQUESTED,
                )
                for a in appointments
                if a.date_time.date() == now.date() and a.status != AppointmentStatus.NO_SHOW
            ],
            waiting_consultation_count=sum(
                1 for a in appointments if a.status == AppointmentStatus.REQUESTED
            ),
            critical_alert_count=sum(1 for p in patients if p.has_critical_alert),
            new_patient_count=sum(
                1 for seen in first_seen.values() if now - seen <= NEW_PATIENT_WINDOW
            ),
            recent_messages=[
                RecentMessagePreview(c.id, c.owner_name, c.last_message_preview, c.last_message_at)
                for c in conversations[:RECENT_MESSAGE_LIMIT]
            ],
        )
