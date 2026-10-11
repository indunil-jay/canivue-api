from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.core.response import APIResponse
from app.features.appointments.domain.repositories import AppointmentRepositoryProtocol
from app.features.appointments.presentation.dependencies import get_appointment_repository
from app.features.assessments.domain.entities import PredictionRepositoryProtocol
from app.features.assessments.presentation.dependencies import get_prediction_repository
from app.features.auth.domain.enums.role import Role
from app.features.auth.presentation.dependencies import require_actor
from app.features.dogs.domain.repositories import DogRepositoryProtocol
from app.features.dogs.presentation.dependencies import get_dog_repository
from app.features.messaging.domain.repositories import ConversationRepositoryProtocol
from app.features.messaging.presentation.dependencies import get_conversation_repository
from app.features.vet_portal.application.use_cases import (
    GetVetDashboardUseCase,
    ListMyPatientsUseCase,
    VetCaseload,
)
from app.shared.actor import Actor

router = APIRouter()

_FROM = ConfigDict(from_attributes=True)


class ScheduleEntryResponse(BaseModel):
    model_config = _FROM

    appointment_id: str
    time: datetime
    owner_name: str
    dog_name: str
    type: str
    confirmed: bool


class RecentMessagePreviewResponse(BaseModel):
    model_config = _FROM

    conversation_id: str
    owner_name: str
    preview: str
    sent_at: datetime


class VetDashboardResponse(BaseModel):
    model_config = _FROM

    vet_name: str
    today_schedule: list[ScheduleEntryResponse]
    waiting_consultation_count: int
    critical_alert_count: int
    new_patient_count: int
    recent_messages: list[RecentMessagePreviewResponse]


class VetPatientResponse(BaseModel):
    model_config = _FROM

    dog_id: str
    dog_name: str
    breed: str
    age_formatted: str
    owner_name: str
    last_visit: datetime | None
    needs_follow_up: bool
    has_critical_alert: bool
    allergies: list[str]
    existing_conditions: list[str]
    current_medications: list[str]


def get_vet_caseload(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
) -> VetCaseload:
    return VetCaseload(appointments, dogs, predictions)


def get_vet_dashboard_use_case(
    caseload: VetCaseload = Depends(get_vet_caseload),
    conversations: ConversationRepositoryProtocol = Depends(get_conversation_repository),
) -> GetVetDashboardUseCase:
    return GetVetDashboardUseCase(caseload, conversations)


def get_list_my_patients_use_case(
    caseload: VetCaseload = Depends(get_vet_caseload),
) -> ListMyPatientsUseCase:
    return ListMyPatientsUseCase(caseload)


@router.get(
    "/dashboard",
    response_model=APIResponse[VetDashboardResponse],
    summary="A veterinarian's day: schedule, counts and recent messages",
)
async def get_vet_dashboard(
    actor: Actor = Depends(require_actor(Role.VET)),
    use_case: GetVetDashboardUseCase = Depends(get_vet_dashboard_use_case),
) -> APIResponse[VetDashboardResponse]:
    summary = await use_case.execute(actor)
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
    use_case: ListMyPatientsUseCase = Depends(get_list_my_patients_use_case),
) -> APIResponse[list[VetPatientResponse]]:
    patients = await use_case.execute(actor)
    return APIResponse(
        message="Patients retrieved successfully",
        data=[VetPatientResponse.model_validate(p) for p in patients],
    )
