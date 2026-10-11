from enum import Enum

from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.appointments.application.use_cases import (
    BookAppointmentInput,
    BookAppointmentUseCase,
    ChangeAppointmentStatusUseCase,
    GetAppointmentUseCase,
    ListDogAppointmentsUseCase,
    ListMyAppointmentsUseCase,
)
from app.features.appointments.domain.entities import AppointmentStatus
from app.features.appointments.presentation.dependencies import (
    get_book_appointment_use_case,
    get_change_appointment_status_use_case,
    get_get_appointment_use_case,
    get_list_dog_appointments_use_case,
    get_list_my_appointments_use_case,
)
from app.features.appointments.presentation.schemas import (
    AppointmentResponse,
    BookAppointmentRequest,
)
from app.features.auth.presentation.dependencies import get_actor
from app.shared.actor import Actor

router = APIRouter()
dog_router = APIRouter()

One = APIResponse[AppointmentResponse]
Many = APIResponse[list[AppointmentResponse]]


class AppointmentAction(str, Enum):
    CONFIRM = "confirm"
    START = "start"
    COMPLETE = "complete"
    NO_SHOW = "no-show"
    CANCEL = "cancel"


_TARGETS = {
    AppointmentAction.CONFIRM: AppointmentStatus.CONFIRMED,
    AppointmentAction.START: AppointmentStatus.IN_PROGRESS,
    AppointmentAction.COMPLETE: AppointmentStatus.COMPLETED,
    AppointmentAction.NO_SHOW: AppointmentStatus.NO_SHOW,
    AppointmentAction.CANCEL: AppointmentStatus.CANCELLED,
}


@dog_router.post(
    "/{dog_id}/appointments",
    response_model=One,
    status_code=status.HTTP_201_CREATED,
    summary="Book an appointment for a Dog",
)
async def book_appointment(
    dog_id: str,
    payload: BookAppointmentRequest,
    actor: Actor = Depends(get_actor),
    use_case: BookAppointmentUseCase = Depends(get_book_appointment_use_case),
) -> One:
    appointment = await use_case.execute(
        actor, BookAppointmentInput(dog_id=dog_id, **payload.model_dump())
    )
    return APIResponse(
        message="Appointment requested successfully",
        data=AppointmentResponse.model_validate(appointment),
    )


@dog_router.get("/{dog_id}/appointments", response_model=Many, summary="List a Dog's appointments")
async def list_dog_appointments(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: ListDogAppointmentsUseCase = Depends(get_list_dog_appointments_use_case),
) -> Many:
    appointments = await use_case.execute(actor, dog_id)
    return APIResponse(
        message="Appointments retrieved successfully",
        data=[AppointmentResponse.model_validate(a) for a in appointments],
    )


@router.get(
    "",
    response_model=Many,
    summary="List my appointments (as the owner, or as the veterinarian)",
)
async def list_my_appointments(
    status: AppointmentStatus | None = None,
    actor: Actor = Depends(get_actor),
    use_case: ListMyAppointmentsUseCase = Depends(get_list_my_appointments_use_case),
) -> Many:
    appointments = await use_case.execute(actor, status)
    return APIResponse(
        message="Appointments retrieved successfully",
        data=[AppointmentResponse.model_validate(a) for a in appointments],
    )


@router.get("/{appointment_id}", response_model=One, summary="Get one appointment")
async def get_appointment(
    appointment_id: str,
    actor: Actor = Depends(get_actor),
    use_case: GetAppointmentUseCase = Depends(get_get_appointment_use_case),
) -> One:
    appointment = await use_case.execute(actor, appointment_id)
    return APIResponse(
        message="Appointment retrieved successfully",
        data=AppointmentResponse.model_validate(appointment),
    )


@router.post(
    "/{appointment_id}/{action}",
    response_model=One,
    summary="Move an appointment on: confirm, start, complete, no-show or cancel",
    description="Owners may only cancel. Veterinarians may perform every action.",
)
async def change_appointment_status(
    appointment_id: str,
    action: AppointmentAction,
    actor: Actor = Depends(get_actor),
    use_case: ChangeAppointmentStatusUseCase = Depends(get_change_appointment_status_use_case),
) -> One:
    appointment = await use_case.execute(actor, appointment_id, _TARGETS[action])
    return APIResponse(
        message="Appointment updated successfully",
        data=AppointmentResponse.model_validate(appointment),
    )
