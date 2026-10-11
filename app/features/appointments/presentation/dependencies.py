from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.appointments.application.use_cases import (
    AppointmentParticipation,
    BookAppointmentUseCase,
    ChangeAppointmentStatusUseCase,
    GetAppointmentUseCase,
    ListDogAppointmentsUseCase,
    ListMyAppointmentsUseCase,
)
from app.features.appointments.domain.repositories import AppointmentRepositoryProtocol
from app.features.appointments.infrastructure.persistence.repositories import (
    SqlAlchemyAppointmentRepository,
)
from app.features.dogs.application.access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.notifications.presentation.dependencies import get_notifier
from app.features.veterinarians.domain.repositories import VetProfileRepositoryProtocol
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


def get_book_appointment_use_case(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
    vets: VetProfileRepositoryProtocol = Depends(get_vet_profile_repository),
    access: DogAccess = Depends(get_dog_access),
    notifier: NotifierProtocol = Depends(get_notifier),
) -> BookAppointmentUseCase:
    return BookAppointmentUseCase(appointments, vets, access, notifier)


def get_list_dog_appointments_use_case(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
    access: DogAccess = Depends(get_dog_access),
) -> ListDogAppointmentsUseCase:
    return ListDogAppointmentsUseCase(appointments, access)


def get_list_my_appointments_use_case(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
) -> ListMyAppointmentsUseCase:
    return ListMyAppointmentsUseCase(appointments)


def get_get_appointment_use_case(
    participation: AppointmentParticipation = Depends(get_appointment_participation),
) -> GetAppointmentUseCase:
    return GetAppointmentUseCase(participation)


def get_change_appointment_status_use_case(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
    participation: AppointmentParticipation = Depends(get_appointment_participation),
    notifier: NotifierProtocol = Depends(get_notifier),
) -> ChangeAppointmentStatusUseCase:
    return ChangeAppointmentStatusUseCase(appointments, participation, notifier)
