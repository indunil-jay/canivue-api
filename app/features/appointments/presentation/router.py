from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.appointments.application.commands.book_appointment.book_appointment_command import (
    BookAppointmentCommand,
)
from app.features.appointments.application.commands.book_appointment.book_appointment_command_handler import (
    BookAppointmentCommandHandler,
)
from app.features.appointments.application.commands.change_appointment_status.change_appointment_status_command import (
    ChangeAppointmentStatusCommand,
)
from app.features.appointments.application.commands.change_appointment_status.change_appointment_status_command_handler import (
    ChangeAppointmentStatusCommandHandler,
)
from app.features.appointments.application.dtos.book_appointment_input import BookAppointmentInput
from app.features.appointments.application.queries.get_appointment.get_appointment_query import (
    GetAppointmentQuery,
)
from app.features.appointments.application.queries.get_appointment.get_appointment_query_handler import (
    GetAppointmentQueryHandler,
)
from app.features.appointments.application.queries.list_dog_appointments.list_dog_appointments_query import (
    ListDogAppointmentsQuery,
)
from app.features.appointments.application.queries.list_dog_appointments.list_dog_appointments_query_handler import (
    ListDogAppointmentsQueryHandler,
)
from app.features.appointments.application.queries.list_my_appointments.list_my_appointments_query import (
    ListMyAppointmentsQuery,
)
from app.features.appointments.application.queries.list_my_appointments.list_my_appointments_query_handler import (
    ListMyAppointmentsQueryHandler,
)
from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.appointments.presentation.dependencies import (
    get_appointment_query_handler,
    get_book_appointment_command_handler,
    get_change_appointment_status_command_handler,
    get_list_dog_appointments_query_handler,
    get_list_my_appointments_query_handler,
)
from app.features.appointments.presentation.requests.appointment_action import AppointmentAction
from app.features.appointments.presentation.requests.book_appointment_request import (
    BookAppointmentRequest,
)
from app.features.appointments.presentation.responses.appointment_response import (
    AppointmentResponse,
)
from app.features.auth.presentation.dependencies import get_actor
from app.shared.actor import Actor

router = APIRouter()


dog_router = APIRouter()


One = APIResponse[AppointmentResponse]


Many = APIResponse[list[AppointmentResponse]]


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
    handler: BookAppointmentCommandHandler = Depends(get_book_appointment_command_handler),
) -> One:
    appointment = await handler.handle(
        BookAppointmentCommand(
            actor=actor, data=BookAppointmentInput(dog_id=dog_id, **payload.model_dump())
        )
    )
    return APIResponse(
        message="Appointment requested successfully",
        data=AppointmentResponse.model_validate(appointment),
    )


@dog_router.get("/{dog_id}/appointments", response_model=Many, summary="List a Dog's appointments")
async def list_dog_appointments(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: ListDogAppointmentsQueryHandler = Depends(get_list_dog_appointments_query_handler),
) -> Many:
    appointments = await handler.handle(ListDogAppointmentsQuery(actor=actor, dog_id=dog_id))
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
    handler: ListMyAppointmentsQueryHandler = Depends(get_list_my_appointments_query_handler),
) -> Many:
    appointments = await handler.handle(ListMyAppointmentsQuery(actor=actor, status=status))
    return APIResponse(
        message="Appointments retrieved successfully",
        data=[AppointmentResponse.model_validate(a) for a in appointments],
    )


@router.get("/{appointment_id}", response_model=One, summary="Get one appointment")
async def get_appointment(
    appointment_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetAppointmentQueryHandler = Depends(get_appointment_query_handler),
) -> One:
    appointment = await handler.handle(
        GetAppointmentQuery(actor=actor, appointment_id=appointment_id)
    )
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
    handler: ChangeAppointmentStatusCommandHandler = Depends(
        get_change_appointment_status_command_handler
    ),
) -> One:
    appointment = await handler.handle(
        ChangeAppointmentStatusCommand(
            actor=actor, appointment_id=appointment_id, target=_TARGETS[action]
        )
    )
    return APIResponse(
        message="Appointment updated successfully",
        data=AppointmentResponse.model_validate(appointment),
    )
