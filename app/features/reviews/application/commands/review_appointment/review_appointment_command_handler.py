from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.appointments.domain.exceptions import AppointmentNotFoundError
from app.features.reviews.application.commands.review_appointment.review_appointment_command import (
    ReviewAppointmentCommand,
)
from app.features.reviews.application.dtos.review_output_dto import ReviewOutputDTO
from app.features.reviews.application.interfaces.repositories.review_repository import (
    ReviewRepositoryProtocol,
)
from app.features.reviews.application.mappers.review_dto_mapper import ReviewDTOMapper
from app.features.reviews.domain.entities.review import Review
from app.features.reviews.domain.exceptions import (
    AlreadyReviewedError,
    AppointmentNotCompletedError,
)


class ReviewAppointmentCommandHandler:
    def __init__(
        self, reviews: ReviewRepositoryProtocol, appointments: AppointmentRepositoryProtocol
    ):
        self._reviews = reviews
        self._appointments = appointments

    async def handle(self, command: ReviewAppointmentCommand) -> ReviewOutputDTO:
        appointment = await self._appointments.get_by_id(command.appointment_id)
        if appointment is None or appointment.owner_id != command.actor.id:
            raise AppointmentNotFoundError()
        if appointment.status != AppointmentStatus.COMPLETED:
            raise AppointmentNotCompletedError()
        if await self._reviews.exists_for_appointment(appointment.id):
            raise AlreadyReviewedError()
        return ReviewDTOMapper.to_output_dto(
            await self._reviews.create(
                Review(
                    appointment_id=appointment.id,
                    vet_id=appointment.vet_id,
                    owner_id=command.actor.id,
                    owner_name=command.actor.display_name,
                    rating=command.rating,
                    comment=command.comment.strip(),
                )
            )
        )
