from fastapi import APIRouter, Depends, Query

from app.core.response import APIResponse
from app.features.auth.domain.enums.role import Role
from app.features.auth.presentation.dependencies import get_actor, require_actor
from app.features.veterinarians.application.commands.set_day_availability.set_day_availability_command import (
    SetDayAvailabilityCommand,
)
from app.features.veterinarians.application.commands.set_day_availability.set_day_availability_command_handler import (
    SetDayAvailabilityCommandHandler,
)
from app.features.veterinarians.application.commands.update_my_vet_profile.update_my_vet_profile_command import (
    UpdateMyVetProfileCommand,
)
from app.features.veterinarians.application.commands.update_my_vet_profile.update_my_vet_profile_command_handler import (
    UpdateMyVetProfileCommandHandler,
)
from app.features.veterinarians.application.commands.verify_veterinarian.verify_veterinarian_command import (
    VerifyVeterinarianCommand,
)
from app.features.veterinarians.application.commands.verify_veterinarian.verify_veterinarian_command_handler import (
    VerifyVeterinarianCommandHandler,
)
from app.features.veterinarians.application.dtos.vet_search_filters import VetSearchFilters
from app.features.veterinarians.application.queries.get_my_availability.get_my_availability_query import (
    GetMyAvailabilityQuery,
)
from app.features.veterinarians.application.queries.get_my_availability.get_my_availability_query_handler import (
    GetMyAvailabilityQueryHandler,
)
from app.features.veterinarians.application.queries.get_my_vet_profile.get_my_vet_profile_query import (
    GetMyVetProfileQuery,
)
from app.features.veterinarians.application.queries.get_my_vet_profile.get_my_vet_profile_query_handler import (
    GetMyVetProfileQueryHandler,
)
from app.features.veterinarians.application.queries.get_veterinarian.get_veterinarian_query import (
    GetVeterinarianQuery,
)
from app.features.veterinarians.application.queries.get_veterinarian.get_veterinarian_query_handler import (
    GetVeterinarianQueryHandler,
)
from app.features.veterinarians.application.queries.list_pending_veterinarians.list_pending_veterinarians_query import (
    ListPendingVeterinariansQuery,
)
from app.features.veterinarians.application.queries.list_pending_veterinarians.list_pending_veterinarians_query_handler import (
    ListPendingVeterinariansQueryHandler,
)
from app.features.veterinarians.application.queries.search_veterinarians.search_veterinarians_query import (
    SearchVeterinariansQuery,
)
from app.features.veterinarians.application.queries.search_veterinarians.search_veterinarians_query_handler import (
    SearchVeterinariansQueryHandler,
)
from app.features.veterinarians.domain.enums.consultation_type import ConsultationType
from app.features.veterinarians.presentation.dependencies import (
    get_list_pending_veterinarians_query_handler,
    get_my_availability_query_handler,
    get_my_vet_profile_query_handler,
    get_search_veterinarians_query_handler,
    get_set_day_availability_command_handler,
    get_update_my_vet_profile_command_handler,
    get_verify_veterinarian_command_handler,
    get_veterinarian_query_handler,
)
from app.features.veterinarians.presentation.mappers import VeterinariansPresentationMapper
from app.features.veterinarians.presentation.requests.set_availability_request import (
    SetAvailabilityRequest,
)
from app.features.veterinarians.presentation.requests.vet_profile_update_request import (
    VetProfileUpdateRequest,
)
from app.features.veterinarians.presentation.responses.veterinarian_response import (
    VeterinarianResponse,
)
from app.shared.actor import Actor

router = APIRouter()


VetResponse = APIResponse[VeterinarianResponse]


VetListResponse = APIResponse[list[VeterinarianResponse]]


AvailabilityResponse = APIResponse[dict[str, bool]]


@router.get("", response_model=VetListResponse, summary="Search verified veterinarians")
async def search_veterinarians(
    q: str = Query("", max_length=100, description="Matches name or specialty"),
    specialty: str | None = Query(None, max_length=100),
    consultation_type: ConsultationType | None = None,
    available_today: bool = False,
    actor: Actor = Depends(get_actor),
    handler: SearchVeterinariansQueryHandler = Depends(get_search_veterinarians_query_handler),
) -> VetListResponse:
    views = await handler.handle(
        SearchVeterinariansQuery(
            filters=VetSearchFilters(
                query=q,
                specialty=specialty,
                consultation_type=consultation_type,
                available_today_only=available_today,
            )
        )
    )
    return APIResponse(
        message="Veterinarians retrieved successfully",
        data=[VeterinariansPresentationMapper.to_veterinarian_response(v) for v in views],
    )


@router.get("/me", response_model=VetResponse, summary="Get my professional profile")
async def get_my_profile(
    actor: Actor = Depends(require_actor(Role.VET)),
    handler: GetMyVetProfileQueryHandler = Depends(get_my_vet_profile_query_handler),
) -> VetResponse:
    view = await handler.handle(GetMyVetProfileQuery(actor=actor))
    return APIResponse(
        message="Profile retrieved successfully",
        data=VeterinariansPresentationMapper.to_veterinarian_response(view),
    )


@router.patch("/me", response_model=VetResponse, summary="Update my professional profile")
async def update_my_profile(
    payload: VetProfileUpdateRequest,
    actor: Actor = Depends(require_actor(Role.VET)),
    handler: UpdateMyVetProfileCommandHandler = Depends(get_update_my_vet_profile_command_handler),
) -> VetResponse:
    view = await handler.handle(UpdateMyVetProfileCommand(actor=actor, changes=payload.to_domain()))
    return APIResponse(
        message="Profile updated successfully",
        data=VeterinariansPresentationMapper.to_veterinarian_response(view),
    )


@router.get(
    "/me/availability", response_model=AvailabilityResponse, summary="Get my weekly availability"
)
async def get_my_availability(
    actor: Actor = Depends(require_actor(Role.VET)),
    handler: GetMyAvailabilityQueryHandler = Depends(get_my_availability_query_handler),
) -> AvailabilityResponse:
    return APIResponse(
        message="Availability retrieved successfully",
        data=await handler.handle(GetMyAvailabilityQuery(actor=actor)),
    )


@router.put(
    "/me/availability/{day}",
    response_model=AvailabilityResponse,
    summary="Set whether I take appointments on a weekday",
)
async def set_day_availability(
    day: str,
    payload: SetAvailabilityRequest,
    actor: Actor = Depends(require_actor(Role.VET)),
    handler: SetDayAvailabilityCommandHandler = Depends(get_set_day_availability_command_handler),
) -> AvailabilityResponse:
    availability = await handler.handle(
        SetDayAvailabilityCommand(actor=actor, day=day, available=payload.available)
    )
    return APIResponse(message="Availability updated successfully", data=availability)


@router.get(
    "/pending", response_model=VetListResponse, summary="List veterinarians awaiting verification"
)
async def list_pending_veterinarians(
    actor: Actor = Depends(require_actor(Role.ADMIN)),
    handler: ListPendingVeterinariansQueryHandler = Depends(
        get_list_pending_veterinarians_query_handler
    ),
) -> VetListResponse:
    views = await handler.handle(ListPendingVeterinariansQuery())
    return APIResponse(
        message="Pending veterinarians retrieved successfully",
        data=[VeterinariansPresentationMapper.to_veterinarian_response(v) for v in views],
    )


@router.post("/{vet_id}/verify", response_model=VetResponse, summary="Verify a veterinarian")
async def verify_veterinarian(
    vet_id: str,
    actor: Actor = Depends(require_actor(Role.ADMIN)),
    handler: VerifyVeterinarianCommandHandler = Depends(get_verify_veterinarian_command_handler),
) -> VetResponse:
    view = await handler.handle(VerifyVeterinarianCommand(vet_id=vet_id))
    return APIResponse(
        message="Veterinarian verified successfully",
        data=VeterinariansPresentationMapper.to_veterinarian_response(view),
    )


@router.get("/{vet_id}", response_model=VetResponse, summary="Get a veterinarian's profile")
async def get_veterinarian(
    vet_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetVeterinarianQueryHandler = Depends(get_veterinarian_query_handler),
) -> VetResponse:
    view = await handler.handle(GetVeterinarianQuery(actor=actor, vet_id=vet_id))
    return APIResponse(
        message="Veterinarian retrieved successfully",
        data=VeterinariansPresentationMapper.to_veterinarian_response(view),
    )
