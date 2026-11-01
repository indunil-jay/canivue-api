from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.file_storage import get_file_storage
from app.features.appointments.infrastructure.services.appointment_patient_registry import (
    AppointmentPatientRegistry,
)
from app.features.auth.infrastructure.services.owner_sharing_policy import (
    UserPrivacySharingPolicy,
)
from app.features.dogs.application.commands.register_dog.register_dog_command_handler import (
    RegisterDogCommandHandler,
)
from app.features.dogs.application.commands.remove_dog.remove_dog_command_handler import (
    RemoveDogCommandHandler,
)
from app.features.dogs.application.commands.remove_dog_photo.remove_dog_photo_command_handler import (
    RemoveDogPhotoCommandHandler,
)
from app.features.dogs.application.commands.set_dog_photo.set_dog_photo_command_handler import (
    SetDogPhotoCommandHandler,
)
from app.features.dogs.application.commands.update_dog.update_dog_command_handler import (
    UpdateDogCommandHandler,
)
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.application.interfaces.services.patient_registry import (
    PatientRegistryProtocol,
)
from app.features.dogs.application.queries.get_dog.get_dog_query_handler import GetDogQueryHandler
from app.features.dogs.application.queries.get_dog_photo.get_dog_photo_query_handler import (
    GetDogPhotoQueryHandler,
)
from app.features.dogs.application.queries.list_my_dogs.list_my_dogs_query_handler import (
    ListMyDogsQueryHandler,
)
from app.features.dogs.application.services.any_patient_registry import AnyPatientRegistry
from app.features.dogs.application.services.consenting_patient_registry import (
    ConsentingPatientRegistry,
)
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.infrastructure.persistence.repositories.dog_repository import (
    SqlAlchemyDogRepository,
)
from app.features.messaging.infrastructure.services.conversation_patient_registry import (
    ConversationPatientRegistry,
)
from app.shared.files import FileStorageProtocol


def get_dog_repository(session: AsyncSession = Depends(get_db_session)) -> DogRepositoryProtocol:
    return SqlAlchemyDogRepository(session=session)


def get_patient_registry(
    session: AsyncSession = Depends(get_db_session),
) -> PatientRegistryProtocol:
    return ConsentingPatientRegistry(
        AnyPatientRegistry(
            AppointmentPatientRegistry(session=session),
            ConversationPatientRegistry(session=session),
        ),
        UserPrivacySharingPolicy(session),
    )


def get_dog_access(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    patients: PatientRegistryProtocol = Depends(get_patient_registry),
) -> DogAccess:
    return DogAccess(dogs=dogs, patients=patients)


def get_register_dog_command_handler(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
) -> RegisterDogCommandHandler:
    return RegisterDogCommandHandler(dogs)


def get_list_my_dogs_query_handler(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
) -> ListMyDogsQueryHandler:
    return ListMyDogsQueryHandler(dogs)


def get_dog_query_handler(access: DogAccess = Depends(get_dog_access)) -> GetDogQueryHandler:
    return GetDogQueryHandler(access)


def get_update_dog_command_handler(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    access: DogAccess = Depends(get_dog_access),
) -> UpdateDogCommandHandler:
    return UpdateDogCommandHandler(dogs, access)


def get_remove_dog_command_handler(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    access: DogAccess = Depends(get_dog_access),
) -> RemoveDogCommandHandler:
    return RemoveDogCommandHandler(dogs, access)


def get_set_dog_photo_command_handler(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> SetDogPhotoCommandHandler:
    return SetDogPhotoCommandHandler(dogs, access, storage)


def get_dog_photo_query_handler(
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> GetDogPhotoQueryHandler:
    return GetDogPhotoQueryHandler(access, storage)


def get_remove_dog_photo_command_handler(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> RemoveDogPhotoCommandHandler:
    return RemoveDogPhotoCommandHandler(dogs, access, storage)
