from app.features.appointments.application.commands.change_appointment_status.change_appointment_status_command import (
    ChangeAppointmentStatusCommand,
)
from app.features.appointments.application.dtos.appointment_output_dto import AppointmentOutputDTO
from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.application.mappers.appointment_dto_mapper import (
    AppointmentDTOMapper,
)
from app.features.appointments.application.services.appointment_participation import (
    AppointmentParticipation,
)
from app.features.appointments.application.services.describe_time import describe_time
from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.shared.notifier import NotificationType, NotifierProtocol

_ANNOUNCED = {
    AppointmentStatus.CONFIRMED: ("Appointment confirmed", "confirmed"),
    AppointmentStatus.CANCELLED: ("Appointment cancelled", "cancelled"),
}


class ChangeAppointmentStatusCommandHandler:
    def __init__(
        self,
        appointments: AppointmentRepositoryProtocol,
        participation: AppointmentParticipation,
        notifier: NotifierProtocol,
    ):
        self._appointments = appointments
        self._participation = participation
        self._notifier = notifier

    async def handle(self, command: ChangeAppointmentStatusCommand) -> AppointmentOutputDTO:
        appointment = await self._participation.load(command.actor, command.appointment_id)
        by_vet = command.actor.id == appointment.vet_user_id or command.actor.is_admin
        appointment.move_to(command.target, by_veterinarian=by_vet)
        appointment = await self._appointments.update(appointment)

        if command.target in _ANNOUNCED:
            title, verb = _ANNOUNCED[command.target]
            acted_as_vet = command.actor.id == appointment.vet_user_id
            recipient = appointment.owner_id if acted_as_vet else appointment.vet_user_id
            who = appointment.vet_name if acted_as_vet else appointment.owner_name
            await self._notifier.notify(
                recipient,
                NotificationType.VET_APPOINTMENT,
                title,
                f"{who} {verb} the appointment for {appointment.dog_name} on {describe_time(appointment)}.",
                dog_name=appointment.dog_name,
                action_label="View Details",
            )
        return AppointmentDTOMapper.to_output_dto(appointment)
