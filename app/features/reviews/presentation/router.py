from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.auth.domain.enums.role import Role
from app.features.auth.presentation.dependencies import get_actor, require_actor
from app.features.reviews.application.commands.review_appointment.review_appointment_command import (
    ReviewAppointmentCommand,
)
from app.features.reviews.application.commands.review_appointment.review_appointment_command_handler import (
    ReviewAppointmentCommandHandler,
)
from app.features.reviews.application.queries.get_my_reputation.get_my_reputation_query import (
    GetMyReputationQuery,
)
from app.features.reviews.application.queries.get_my_reputation.get_my_reputation_query_handler import (
    GetMyReputationQueryHandler,
)
from app.features.reviews.application.queries.list_vet_reviews.list_vet_reviews_query import (
    ListVetReviewsQuery,
)
from app.features.reviews.application.queries.list_vet_reviews.list_vet_reviews_query_handler import (
    ListVetReviewsQueryHandler,
)
from app.features.reviews.presentation.dependencies import (
    get_list_vet_reviews_query_handler,
    get_my_reputation_query_handler,
    get_review_appointment_command_handler,
)
from app.features.reviews.presentation.requests.review_request import ReviewRequest
from app.features.reviews.presentation.responses.patient_review_response import (
    PatientReviewResponse,
)
from app.features.reviews.presentation.responses.vet_reputation_response import (
    VetReputationResponse,
)
from app.shared.actor import Actor

router = APIRouter()


@router.post(
    "/reviews",
    response_model=APIResponse[PatientReviewResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Review the veterinarian of a completed appointment",
)
async def review_appointment(
    payload: ReviewRequest,
    actor: Actor = Depends(get_actor),
    handler: ReviewAppointmentCommandHandler = Depends(get_review_appointment_command_handler),
) -> APIResponse[PatientReviewResponse]:
    review = await handler.handle(
        ReviewAppointmentCommand(
            actor=actor,
            appointment_id=payload.appointment_id,
            rating=payload.rating,
            comment=payload.comment,
        )
    )
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
    handler: GetMyReputationQueryHandler = Depends(get_my_reputation_query_handler),
) -> APIResponse[VetReputationResponse]:
    reputation = await handler.handle(GetMyReputationQuery(actor=actor))
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
    handler: ListVetReviewsQueryHandler = Depends(get_list_vet_reviews_query_handler),
) -> APIResponse[list[PatientReviewResponse]]:
    reviews = await handler.handle(ListVetReviewsQuery(vet_id=vet_id))
    return APIResponse(
        message="Reviews retrieved successfully",
        data=[PatientReviewResponse.model_validate(r) for r in reviews],
    )
