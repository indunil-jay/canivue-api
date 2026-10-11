from collections.abc import Sequence

from app.features.appointments.domain.entities import AppointmentStatus
from app.features.appointments.domain.exceptions import AppointmentNotFoundError
from app.features.appointments.domain.repositories import AppointmentRepositoryProtocol
from app.features.reviews.domain.entities import (
    AlreadyReviewedError,
    AppointmentNotCompletedError,
    Review,
    ReviewRepositoryProtocol,
    VetReputation,
)
from app.features.veterinarians.domain.exceptions import VeterinarianNotFoundError
from app.features.veterinarians.domain.repositories import (
    VetProfileRepositoryProtocol,
    VetStatsProviderProtocol,
)
from app.shared.actor import Actor


class ReviewAppointmentUseCase:
    def __init__(
        self, reviews: ReviewRepositoryProtocol, appointments: AppointmentRepositoryProtocol
    ):
        self._reviews = reviews
        self._appointments = appointments

    async def execute(self, actor: Actor, appointment_id: str, rating: int, comment: str) -> Review:
        appointment = await self._appointments.get_by_id(appointment_id)
        if appointment is None or appointment.owner_id != actor.id:
            raise AppointmentNotFoundError()
        if appointment.status != AppointmentStatus.COMPLETED:
            raise AppointmentNotCompletedError()
        if await self._reviews.exists_for_appointment(appointment.id):
            raise AlreadyReviewedError()
        return await self._reviews.create(
            Review(
                appointment_id=appointment.id,
                vet_id=appointment.vet_id,
                owner_id=actor.id,
                owner_name=actor.display_name,
                rating=rating,
                comment=comment.strip(),
            )
        )


class ListVetReviewsUseCase:
    def __init__(self, reviews: ReviewRepositoryProtocol, vets: VetProfileRepositoryProtocol):
        self._reviews = reviews
        self._vets = vets

    async def execute(self, vet_id: str) -> Sequence[Review]:
        vet = await self._vets.get_by_id(vet_id)
        if vet is None or not vet.verified:
            raise VeterinarianNotFoundError()
        return await self._reviews.list_for_vet(vet.id)


class GetMyReputationUseCase:
    def __init__(
        self,
        reviews: ReviewRepositoryProtocol,
        vets: VetProfileRepositoryProtocol,
        stats: VetStatsProviderProtocol,
    ):
        self._reviews = reviews
        self._vets = vets
        self._stats = stats

    async def execute(self, actor: Actor) -> VetReputation:
        vet = await self._vets.get_by_user_id(actor.id)
        if vet is None:
            raise VeterinarianNotFoundError()
        stats = (await self._stats.stats_for([vet.id]))[vet.id]
        return VetReputation(
            average_rating=stats.rating,
            total_consultations=stats.consultation_count,
            recommendations_accepted_percent=stats.recommendations_accepted_percent,
            repeat_consultation_percent=stats.follow_up_rate_percent,
            reviews=await self._reviews.list_for_vet(vet.id),
        )
