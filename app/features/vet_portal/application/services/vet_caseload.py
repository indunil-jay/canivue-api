from datetime import datetime, timezone

from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.domain.entities.appointment import Appointment
from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.domain.enums.prediction_status import PredictionStatus
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.vet_portal.application.dtos.vet_patient import VetPatient
from app.shared.actor import Actor

_CRITICAL = {PredictionStatus.HIGH_RISK, PredictionStatus.VET_REVIEW_RECOMMENDED}


_NEEDS_ATTENTION = _CRITICAL | {PredictionStatus.MODERATE_RISK}


_LIVE = {AppointmentStatus.REQUESTED, AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS}


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
