from datetime import datetime, timezone

from app.features.appointments.application.commands.book_appointment.book_appointment_command import (
    BookAppointmentCommand,
)
from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.application.services.describe_time import describe_time
from app.features.appointments.domain.entities.appointment import Appointment
from app.features.appointments.domain.exceptions import BookingRejectedError, SlotTakenError
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.domain.exceptions import VeterinarianNotFoundError
from app.shared.notifier import NotificationType, NotifierProtocol


def _as_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


class BookAppointmentCommandHandler:
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

    async def handle(self, command: BookAppointmentCommand) -> Appointment:
        dog = await self._access.owned(command.actor, command.data.dog_id)
        vet = await self._vets.get_by_id(command.data.vet_id)
        if vet is None or not vet.verified:
            raise VeterinarianNotFoundError()

        when = _as_utc(command.data.date_time).replace(second=0, microsecond=0)
        if when <= datetime.now(timezone.utc):
            raise BookingRejectedError("An appointment must be in the future.")
        if not vet.is_available_on(when):
            raise BookingRejectedError(f"{vet.name} does not take appointments on that day.")
        if not vet.offers(command.data.consultation_type):
            raise BookingRejectedError(f"{vet.name} does not offer that consultation type.")
        if await self._appointments.slot_is_taken(vet.id, when):
            raise SlotTakenError()

        appointment = await self._appointments.create(
            Appointment(
                owner_id=dog.owner_id,
                owner_name=command.actor.display_name,
                vet_id=vet.id,
                vet_user_id=vet.user_id,
                vet_name=vet.name,
                dog_id=dog.id,
                dog_name=dog.name,
                date_time=when,
                consultation_type=command.data.consultation_type,
                # The published fee, never a client-supplied one.
                fee_usd=vet.consultation_fee_usd,
                notes=command.data.notes,
            )
        )
        await self._notifier.notify(
            vet.user_id,
            NotificationType.VET_APPOINTMENT,
            "New appointment request",
            f"{appointment.owner_name} requested an appointment for {dog.name} "
            f"on {describe_time(appointment)}.",
            dog_name=dog.name,
            action_label="View Details",
        )
        return appointment
