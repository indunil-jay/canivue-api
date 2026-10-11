from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.file_storage import get_file_storage
from app.features.appointments.infrastructure.persistence.repositories import (
    AppointmentPatientRegistry,
)
from app.features.dogs.application.access import AnyPatientRegistry, DogAccess
from app.features.dogs.application.use_cases import (
    GetDogPhotoUseCase,
    GetDogUseCase,
    ListMyDogsUseCase,
    RegisterDogUseCase,
    RemoveDogPhotoUseCase,
    RemoveDogUseCase,
    SetDogPhotoUseCase,
    UpdateDogUseCase,
)
from app.features.dogs.domain.repositories import DogRepositoryProtocol, PatientRegistryProtocol
from app.features.dogs.infrastructure.persistence.repositories import SqlAlchemyDogRepository
from app.features.messaging.infrastructure.persistence.repositories import (
    ConversationPatientRegistry,
)
from app.shared.files import FileStorageProtocol


def get_dog_repository(session: AsyncSession = Depends(get_db_session)) -> DogRepositoryProtocol:
    return SqlAlchemyDogRepository(session=session)


def get_patient_registry(
    session: AsyncSession = Depends(get_db_session),
) -> PatientRegistryProtocol:
    return AnyPatientRegistry(
        AppointmentPatientRegistry(session=session),
        ConversationPatientRegistry(session=session),
    )


def get_dog_access(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    patients: PatientRegistryProtocol = Depends(get_patient_registry),
) -> DogAccess:
    return DogAccess(dogs=dogs, patients=patients)


def get_register_dog_use_case(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
) -> RegisterDogUseCase:
    return RegisterDogUseCase(dogs)


def get_list_my_dogs_use_case(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
) -> ListMyDogsUseCase:
    return ListMyDogsUseCase(dogs)


def get_get_dog_use_case(access: DogAccess = Depends(get_dog_access)) -> GetDogUseCase:
    return GetDogUseCase(access)


def get_update_dog_use_case(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    access: DogAccess = Depends(get_dog_access),
) -> UpdateDogUseCase:
    return UpdateDogUseCase(dogs, access)


def get_remove_dog_use_case(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    access: DogAccess = Depends(get_dog_access),
) -> RemoveDogUseCase:
    return RemoveDogUseCase(dogs, access)


def get_set_dog_photo_use_case(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> SetDogPhotoUseCase:
    return SetDogPhotoUseCase(dogs, access, storage)


def get_get_dog_photo_use_case(
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> GetDogPhotoUseCase:
    return GetDogPhotoUseCase(access, storage)


def get_remove_dog_photo_use_case(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> RemoveDogPhotoUseCase:
    return RemoveDogPhotoUseCase(dogs, access, storage)
