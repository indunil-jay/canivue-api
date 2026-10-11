from app.features.dogs.application.services.dog_access import DogAccess
from app.features.medical_records.application.commands.delete_medical_record.delete_medical_record_command import (
    DeleteMedicalRecordCommand,
)
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.medical_records.application.services.record_lookup import _RecordLookup
from app.features.medical_records.domain.exceptions import (
    NotRecordAuthorError,
)
from app.shared.files import (
    FileStorageProtocol,
)


class DeleteMedicalRecordCommandHandler(_RecordLookup):
    def __init__(
        self,
        records: MedicalRecordRepositoryProtocol,
        access: DogAccess,
        storage: FileStorageProtocol,
    ):
        super().__init__(records, access)
        self._storage = storage

    async def handle(self, command: DeleteMedicalRecordCommand) -> None:
        record = await self._load(command.actor, command.dog_id, command.record_id)
        if record.author_user_id != command.actor.id and not command.actor.is_admin:
            raise NotRecordAuthorError()
        await self._records.delete(record.id)
        if record.file_id:
            await self._storage.delete(record.file_id)
