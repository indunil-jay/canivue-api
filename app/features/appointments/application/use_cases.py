from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone

from app.features.appointments.domain.entities import Appointment, AppointmentStatus
from app.features.appointments.domain.exceptions import (
    AppointmentNotFoundError,
    BookingRejectedError,
    SlotTakenError,
)
from app.features.appointments.domain.repositories import AppointmentRepositoryProtocol
from app.features.dogs.application.access import DogAccess
from app.features.veterinarians.domain.entities import ConsultationType
from app.features.veterinarians.domain.exceptions import VeterinarianNotFoundError
from app.features.veterinarians.domain.repositories import VetProfileRepositoryProtocol
from app.shared.actor import Actor
from app.shared.notifier import NotificationType, NotifierProtocol


@dataclass(frozen=True)
class BookAppointmentInput:
    dog_id: str
    vet_id: str
    date_time: datetime
    consultation_type: ConsultationType
    notes: str = ""


def _as_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _when(appointment: Appointment) -> str:
    return appointment.date_time.strftime("%a %d %b at %H:%M UTC")


class BookAppointmentUseCase:
    def __init__(
        self,
        appointments: AppointmentRepositoryProtocol,
        vets: VetProfileRepositoryProtocol,
        access: DogAccess,
        notifier: NotifierProtocol,
    ):
        self._appointments = appointments
        self._vets = vets
        self._access = access
        self._notifier = notifier

    async def execute(self, actor: Actor, data: BookAppointmentInput) -> Appointment:
        dog = await self._access.owned(actor, data.dog_id)
        vet = await self._vets.get_by_id(data.vet_id)
        if vet is None or not vet.verified:
            raise VeterinarianNotFoundError()

        when = _as_utc(data.date_time).replace(second=0, microsecond=0)
        if when <= datetime.now(timezone.utc):
            raise BookingRejectedError("An appointment must be in the future.")
        if not vet.is_available_on(when):
            raise BookingRejectedError(f"{vet.name} does not take appointments on that day.")
        if not vet.offers(data.consultation_type):
            raise BookingRejectedError(f"{vet.name} does not offer that consultation type.")
        if await self._appointments.slot_is_taken(vet.id, when):
            raise SlotTakenError()

        appointment = await self._appointments.create(
            Appointment(
                owner_id=dog.owner_id,
                owner_name=actor.display_name,
                vet_id=vet.id,
                vet_user_id=vet.user_id,
                vet_name=vet.name,
                dog_id=dog.id,
                dog_name=dog.name,
                date_time=when,
                consultation_type=data.consultation_type,
                # The published fee, never a client-supplied one.
                fee_usd=vet.consultation_fee_usd,
                notes=data.notes,
            )
        )
        await self._notifier.notify(
            vet.user_id,
            NotificationType.VET_APPOINTMENT,
            "New appointment request",
            f"{appointment.owner_name} requested an appointment for {dog.name} "
            f"on {_when(appointment)}.",
            dog_name=dog.name,
            action_label="View Details",
        )
        return appointment


class ListDogAppointmentsUseCase:
    def __init__(self, appointments: AppointmentRepositoryProtocol, access: DogAccess):
        self._appointments = appointments
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> Sequence[Appointment]:
        dog = await self._access.readable(actor, dog_id)
        appointments = await self._appointments.list_for_dog(dog.id)
        if actor.is_vet and dog.owner_id != actor.id:
            # A treating veterinarian sees their own appointments, not the Dog's other vets'.
            return [a for a in appointments if a.vet_user_id == actor.id]
        return appointments


class ListMyAppointmentsUseCase:
    def __init__(self, appointments: AppointmentRepositoryProtocol):
        self._appointments = appointments

    async def execute(
        self, actor: Actor, status: AppointmentStatus | None = None
    ) -> Sequence[Appointment]:
        if actor.is_vet:
            mine = await self._appointments.list_for_vet_user(actor.id)
        else:
            mine = await self._appointments.list_for_owner(actor.id)
        return [a for a in mine if status is None or a.status == status]


class AppointmentParticipation:
    def __init__(self, appointments: AppointmentRepositoryProtocol):
        self._appointments = appointments

    async def load(self, actor: Actor, appointment_id: str) -> Appointment:
        appointment = await self._appointments.get_by_id(appointment_id)
        if appointment is None or not (
            actor.is_admin or actor.id in (appointment.owner_id, appointment.vet_user_id)
        ):
            raise AppointmentNotFoundError()
        return appointment


class GetAppointmentUseCase:
    def __init__(self, participation: AppointmentParticipation):
        self._participation = participation

    async def execute(self, actor: Actor, appointment_id: str) -> Appointment:
        return await self._participation.load(actor, appointment_id)


_ANNOUNCED = {
    AppointmentStatus.CONFIRMED: ("Appointment confirmed", "confirmed"),
    AppointmentStatus.CANCELLED: ("Appointment cancelled", "cancelled"),
}


class ChangeAppointmentStatusUseCase:
    def __init__(
        self,
        appointments: AppointmentRepositoryProtocol,
        participation: AppointmentParticipation,
        notifier: NotifierProtocol,
    ):
        self._appointments = appointments
        self._participation = participation
        self._notifier = notifier

    async def execute(
        self, actor: Actor, appointment_id: str, target: AppointmentStatus
    ) -> Appointment:
        appointment = await self._participation.load(actor, appointment_id)
        by_vet = actor.id == appointment.vet_user_id or actor.is_admin
        appointment.move_to(target, by_veterinarian=by_vet)
        appointment = await self._appointments.update(appointment)

        if target in _ANNOUNCED:
            title, verb = _ANNOUNCED[target]
            acted_as_vet = actor.id == appointment.vet_user_id
            recipient = appointment.owner_id if acted_as_vet else appointment.vet_user_id
            who = appointment.vet_name if acted_as_vet else appointment.owner_name
            await self._notifier.notify(
                recipient,
                NotificationType.VET_APPOINTMENT,
                title,
                f"{who} {verb} the appointment for {appointment.dog_name} on {_when(appointment)}.",
                dog_name=appointment.dog_name,
                action_label="View Details",
            )
        return appointment
