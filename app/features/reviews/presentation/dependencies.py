from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.presentation.dependencies import get_appointment_repository
from app.features.reviews.application.commands.review_appointment.review_appointment_command_handler import (
    ReviewAppointmentCommandHandler,
)
from app.features.reviews.application.interfaces.repositories.review_repository import (
    ReviewRepositoryProtocol,
)
from app.features.reviews.application.queries.get_my_reputation.get_my_reputation_query_handler import (
    GetMyReputationQueryHandler,
)
from app.features.reviews.application.queries.list_vet_reviews.list_vet_reviews_query_handler import (
    ListVetReviewsQueryHandler,
)
from app.features.reviews.infrastructure.persistence.repositories.review_repository import (
    SqlAlchemyReviewRepository,
)
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.application.interfaces.services.vet_stats_provider import (
    VetStatsProviderProtocol,
)
from app.features.veterinarians.presentation.dependencies import (
    get_vet_profile_repository,
    get_vet_stats_provider,
)


def get_review_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ReviewRepositoryProtocol:
    return SqlAlchemyReviewRepository(session=session)


def get_review_appointment_command_handler(
    reviews: ReviewRepositoryProtocol = Depends(get_review_repository),
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
) -> ReviewAppointmentCommandHandler:
    return ReviewAppointmentCommandHandler(reviews, appointments)


def get_list_vet_reviews_query_handler(
    reviews: ReviewRepositoryProtocol = Depends(get_review_repository),
    vets: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
) -> ListVetReviewsQueryHandler:
    return ListVetReviewsQueryHandler(reviews, vets)


def get_my_reputation_query_handler(
    reviews: ReviewRepositoryProtocol = Depends(get_review_repository),
    vets: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    stats: VetStatsProviderProtocol = Depends(get_vet_stats_provider),
) -> GetMyReputationQueryHandler:
    return GetMyReputationQueryHandler(reviews, vets, stats)
