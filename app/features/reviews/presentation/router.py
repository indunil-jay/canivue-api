from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.response import APIResponse
from app.features.appointments.domain.repositories import AppointmentRepositoryProtocol
from app.features.appointments.presentation.dependencies import get_appointment_repository
from app.features.auth.domain.enums.role import Role
from app.features.auth.presentation.dependencies import get_actor, require_actor
from app.features.reviews.application.use_cases import (
    GetMyReputationUseCase,
    ListVetReviewsUseCase,
    ReviewAppointmentUseCase,
)
from app.features.reviews.domain.entities import ReviewRepositoryProtocol
from app.features.reviews.infrastructure.persistence.repositories import (
    SqlAlchemyReviewRepository,
)
from app.features.veterinarians.domain.repositories import (
    VetProfileRepositoryProtocol,
    VetStatsProviderProtocol,
)
from app.features.veterinarians.presentation.dependencies import (
    get_vet_profile_repository,
    get_vet_stats_provider,
)
from app.shared.actor import Actor

router = APIRouter()

_FROM = ConfigDict(from_attributes=True)


class ReviewRequest(BaseModel):
    appointment_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field("", max_length=2000)


class PatientReviewResponse(BaseModel):
    model_config = _FROM

    owner_name: str
    rating: int
    comment: str
    date: datetime


class VetReputationResponse(BaseModel):
    model_config = _FROM

    average_rating: float
    total_consultations: int
    recommendations_accepted_percent: int = Field(..., description="Not tracked yet; always 0.")
    repeat_consultation_percent: int
    reviews: list[PatientReviewResponse]


def get_review_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ReviewRepositoryProtocol:
    return SqlAlchemyReviewRepository(session=session)


def get_review_appointment_use_case(
    reviews: ReviewRepositoryProtocol = Depends(get_review_repository),
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
) -> ReviewAppointmentUseCase:
    return ReviewAppointmentUseCase(reviews, appointments)


def get_list_vet_reviews_use_case(
    reviews: ReviewRepositoryProtocol = Depends(get_review_repository),
    vets: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
) -> ListVetReviewsUseCase:
    return ListVetReviewsUseCase(reviews, vets)


def get_my_reputation_use_case(
    reviews: ReviewRepositoryProtocol = Depends(get_review_repository),
    vets: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    stats: VetStatsProviderProtocol = Depends(get_vet_stats_provider),
) -> GetMyReputationUseCase:
    return GetMyReputationUseCase(reviews, vets, stats)


@router.post(
    "/reviews",
    response_model=APIResponse[PatientReviewResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Review the veterinarian of a completed appointment",
)
async def review_appointment(
    payload: ReviewRequest,
    actor: Actor = Depends(get_actor),
    use_case: ReviewAppointmentUseCase = Depends(get_review_appointment_use_case),
) -> APIResponse[PatientReviewResponse]:
    review = await use_case.execute(actor, payload.appointment_id, payload.rating, payload.comment)
    return APIResponse(
        message="Review submitted", data=PatientReviewResponse.model_validate(review)
    )


@router.get(
    "/veterinarians/me/reputation",
    response_model=APIResponse[VetReputationResponse],
    summary="Get my reputation summary and reviews",
)
async def get_my_reputation(
    actor: Actor = Depends(require_actor(Role.VET)),
    use_case: GetMyReputationUseCase = Depends(get_my_reputation_use_case),
) -> APIResponse[VetReputationResponse]:
    reputation = await use_case.execute(actor)
    return APIResponse(
        message="Reputation retrieved successfully",
        data=VetReputationResponse.model_validate(reputation),
    )


@router.get(
    "/veterinarians/{vet_id}/reviews",
    response_model=APIResponse[list[PatientReviewResponse]],
    summary="List a veterinarian's reviews, newest first",
)
async def list_vet_reviews(
    vet_id: str,
    actor: Actor = Depends(get_actor),
    use_case: ListVetReviewsUseCase = Depends(get_list_vet_reviews_use_case),
) -> APIResponse[list[PatientReviewResponse]]:
    reviews = await use_case.execute(vet_id)
    return APIResponse(
        message="Reviews retrieved successfully",
        data=[PatientReviewResponse.model_validate(r) for r in reviews],
    )
