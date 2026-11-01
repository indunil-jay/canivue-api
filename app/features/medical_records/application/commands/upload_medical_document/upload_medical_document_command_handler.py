from app.features.dogs.application.services.dog_access import DogAccess
from app.features.medical_records.application.commands.upload_medical_document.upload_medical_document_command import (
    UploadMedicalDocumentCommand,
)
from app.features.medical_records.application.dtos.medical_record_output_dto import (
    MedicalRecordOutputDTO,
)
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.medical_records.application.mappers.medical_record_dto_mapper import (
    MedicalRecordDTOMapper,
)
from app.features.medical_records.domain.entities.medical_record import MedicalRecord
from app.features.medical_records.domain.enums.medical_record_type import MedicalRecordType
from app.shared.files import (
    DOCUMENT_TYPES,
    FileStorageProtocol,
    validate_upload,
)


class UploadMedicalDocumentCommandHandler:
    def __init__(
        self,
        records: MedicalRecordRepositoryProtocol,
        access: DogAccess,
        storage: FileStorageProtocol,
    ):
        self._records = records
        self._access = access
        self._storage = storage

    async def handle(self, command: UploadMedicalDocumentCommand) -> MedicalRecordOutputDTO:
        dog = await self._access.readable(command.actor, command.dog_id)
        accepted_type = validate_upload(
            command.content, command.content_type, DOCUMENT_TYPES, command.max_bytes
        )
        file_id = await self._storage.save(command.content, accepted_type)
        return MedicalRecordDTOMapper.to_output_dto(
            await self._records.create(
                MedicalRecord(
                    dog_id=dog.id,
                    type=MedicalRecordType.DOCUMENT,
                    title=command.title.strip(),
                    description="Uploaded document",
                    file_id=file_id,
                    author_user_id=command.actor.id,
                    author_name=command.actor.display_name,
                    authored_by_vet=command.actor.is_vet and dog.owner_id != command.actor.id,
                )
            )
        )
