from fastapi import APIRouter, Depends, Query

from app.core.response import APIResponse
from app.features.auth.domain.enums.role import Role
from app.features.auth.presentation.dependencies import get_actor, require_actor
from app.features.veterinarians.application.use_cases import (
    GetMyAvailabilityUseCase,
    GetMyVetProfileUseCase,
    GetVeterinarianUseCase,
    ListPendingVeterinariansUseCase,
    SearchVeterinariansUseCase,
    SetDayAvailabilityUseCase,
    UpdateMyVetProfileUseCase,
    VerifyVeterinarianUseCase,
    VetSearchFilters,
)
from app.features.veterinarians.domain.entities import ConsultationType
from app.features.veterinarians.presentation.dependencies import (
    get_get_veterinarian_use_case,
    get_list_pending_veterinarians_use_case,
    get_my_availability_use_case,
    get_my_vet_profile_use_case,
    get_search_veterinarians_use_case,
    get_set_day_availability_use_case,
    get_update_my_vet_profile_use_case,
    get_verify_veterinarian_use_case,
)
from app.features.veterinarians.presentation.schemas import (
    SetAvailabilityRequest,
    VeterinarianResponse,
    VetProfileUpdateRequest,
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
    use_case: SearchVeterinariansUseCase = Depends(get_search_veterinarians_use_case),
) -> VetListResponse:
    views = await use_case.execute(
        VetSearchFilters(
            query=q,
            specialty=specialty,
            consultation_type=consultation_type,
            available_today_only=available_today,
        )
    )
    return APIResponse(
        message="Veterinarians retrieved successfully",
        data=[VeterinarianResponse.from_view(v) for v in views],
    )


@router.get("/me", response_model=VetResponse, summary="Get my professional profile")
async def get_my_profile(
    actor: Actor = Depends(require_actor(Role.VET)),
    use_case: GetMyVetProfileUseCase = Depends(get_my_vet_profile_use_case),
) -> VetResponse:
    view = await use_case.execute(actor)
    return APIResponse(
        message="Profile retrieved successfully", data=VeterinarianResponse.from_view(view)
    )


@router.patch("/me", response_model=VetResponse, summary="Update my professional profile")
async def update_my_profile(
    payload: VetProfileUpdateRequest,
    actor: Actor = Depends(require_actor(Role.VET)),
    use_case: UpdateMyVetProfileUseCase = Depends(get_update_my_vet_profile_use_case),
) -> VetResponse:
    view = await use_case.execute(actor, payload.to_domain())
    return APIResponse(
        message="Profile updated successfully", data=VeterinarianResponse.from_view(view)
    )


@router.get(
    "/me/availability", response_model=AvailabilityResponse, summary="Get my weekly availability"
)
async def get_my_availability(
    actor: Actor = Depends(require_actor(Role.VET)),
    use_case: GetMyAvailabilityUseCase = Depends(get_my_availability_use_case),
) -> AvailabilityResponse:
    return APIResponse(
        message="Availability retrieved successfully", data=await use_case.execute(actor)
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
    use_case: SetDayAvailabilityUseCase = Depends(get_set_day_availability_use_case),
) -> AvailabilityResponse:
    availability = await use_case.execute(actor, day, payload.available)
    return APIResponse(message="Availability updated successfully", data=availability)


@router.get(
    "/pending", response_model=VetListResponse, summary="List veterinarians awaiting verification"
)
async def list_pending_veterinarians(
    actor: Actor = Depends(require_actor(Role.ADMIN)),
    use_case: ListPendingVeterinariansUseCase = Depends(get_list_pending_veterinarians_use_case),
) -> VetListResponse:
    views = await use_case.execute()
    return APIResponse(
        message="Pending veterinarians retrieved successfully",
        data=[VeterinarianResponse.from_view(v) for v in views],
    )


@router.post("/{vet_id}/verify", response_model=VetResponse, summary="Verify a veterinarian")
async def verify_veterinarian(
    vet_id: str,
    actor: Actor = Depends(require_actor(Role.ADMIN)),
    use_case: VerifyVeterinarianUseCase = Depends(get_verify_veterinarian_use_case),
) -> VetResponse:
    view = await use_case.execute(vet_id)
    return APIResponse(
        message="Veterinarian verified successfully", data=VeterinarianResponse.from_view(view)
    )


@router.get("/{vet_id}", response_model=VetResponse, summary="Get a veterinarian's profile")
async def get_veterinarian(
    vet_id: str,
    actor: Actor = Depends(get_actor),
    use_case: GetVeterinarianUseCase = Depends(get_get_veterinarian_use_case),
) -> VetResponse:
    view = await use_case.execute(actor, vet_id)
    return APIResponse(
        message="Veterinarian retrieved successfully", data=VeterinarianResponse.from_view(view)
    )
