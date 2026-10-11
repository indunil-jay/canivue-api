from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.appointments.application.commands.book_appointment.book_appointment_command_handler import (
    BookAppointmentCommandHandler,
)
from app.features.appointments.application.commands.change_appointment_status.change_appointment_status_command_handler import (
    ChangeAppointmentStatusCommandHandler,
)
from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.application.queries.get_appointment.get_appointment_query_handler import (
    GetAppointmentQueryHandler,
)
from app.features.appointments.application.queries.list_dog_appointments.list_dog_appointments_query_handler import (
    ListDogAppointmentsQueryHandler,
)
from app.features.appointments.application.queries.list_my_appointments.list_my_appointments_query_handler import (
    ListMyAppointmentsQueryHandler,
)
from app.features.appointments.application.services.appointment_participation import (
    AppointmentParticipation,
)
from app.features.appointments.infrastructure.persistence.repositories.appointment_repository import (
    SqlAlchemyAppointmentRepository,
)
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.notifications.presentation.dependencies import get_notifier
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.presentation.dependencies import get_vet_profile_repository
from app.shared.notifier import NotifierProtocol


def get_appointment_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AppointmentRepositoryProtocol:
    return SqlAlchemyAppointmentRepository(session=session)


def get_appointment_participation(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
) -> AppointmentParticipation:
    return AppointmentParticipation(appointments)


def get_book_appointment_command_handler(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
    vets: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    access: DogAccess = Depends(get_dog_access),
    notifier: NotifierProtocol = Depends(get_notifier),
) -> BookAppointmentCommandHandler:
    return BookAppointmentCommandHandler(appointments, vets, access, notifier)


def get_list_dog_appointments_query_handler(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
    access: DogAccess = Depends(get_dog_access),
) -> ListDogAppointmentsQueryHandler:
    return ListDogAppointmentsQueryHandler(appointments, access)


def get_list_my_appointments_query_handler(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
) -> ListMyAppointmentsQueryHandler:
    return ListMyAppointmentsQueryHandler(appointments)


def get_appointment_query_handler(
    participation: AppointmentParticipation = Depends(get_appointment_participation),
) -> GetAppointmentQueryHandler:
    return GetAppointmentQueryHandler(participation)


def get_change_appointment_status_command_handler(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
    participation: AppointmentParticipation = Depends(get_appointment_participation),
    notifier: NotifierProtocol = Depends(get_notifier),
) -> ChangeAppointmentStatusCommandHandler:
    return ChangeAppointmentStatusCommandHandler(appointments, participation, notifier)
