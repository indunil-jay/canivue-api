from fastapi import APIRouter, Depends

from app.core.response import APIResponse
from app.features.auth.domain.enums.role import Role
from app.features.auth.presentation.dependencies import require_actor
from app.features.vet_portal.application.queries.get_vet_dashboard.get_vet_dashboard_query import (
    GetVetDashboardQuery,
)
from app.features.vet_portal.application.queries.get_vet_dashboard.get_vet_dashboard_query_handler import (
    GetVetDashboardQueryHandler,
)
from app.features.vet_portal.application.queries.list_my_patients.list_my_patients_query import (
    ListMyPatientsQuery,
)
from app.features.vet_portal.application.queries.list_my_patients.list_my_patients_query_handler import (
    ListMyPatientsQueryHandler,
)
from app.features.vet_portal.presentation.dependencies import (
    get_list_my_patients_query_handler,
    get_vet_dashboard_query_handler,
)
from app.features.vet_portal.presentation.responses.vet_dashboard_response import (
    VetDashboardResponse,
)
from app.features.vet_portal.presentation.responses.vet_patient_response import VetPatientResponse
from app.shared.actor import Actor

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=APIResponse[VetDashboardResponse],
    summary="A veterinarian's day: schedule, counts and recent messages",
)
async def get_vet_dashboard(
    actor: Actor = Depends(require_actor(Role.VET)),
    handler: GetVetDashboardQueryHandler = Depends(get_vet_dashboard_query_handler),
) -> APIResponse[VetDashboardResponse]:
    summary = await handler.handle(GetVetDashboardQuery(actor=actor))
    return APIResponse(
        message="Dashboard retrieved successfully",
        data=VetDashboardResponse.model_validate(summary),
    )


@router.get(
    "/patients",
    response_model=APIResponse[list[VetPatientResponse]],
    summary="A veterinarian's patients, critical alerts first",
)
async def list_my_patients(
    actor: Actor = Depends(require_actor(Role.VET)),
    handler: ListMyPatientsQueryHandler = Depends(get_list_my_patients_query_handler),
) -> APIResponse[list[VetPatientResponse]]:
    patients = await handler.handle(ListMyPatientsQuery(actor=actor))
    return APIResponse(
        message="Patients retrieved successfully",
        data=[VetPatientResponse.model_validate(p) for p in patients],
    )
