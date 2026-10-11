from app.features.dogs.application.services.dog_access import DogAccess
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.medical_records.application.queries.get_record_attachment.get_record_attachment_query import (
    GetRecordAttachmentQuery,
)
from app.features.medical_records.application.services.record_lookup import _RecordLookup
from app.shared.files import (
    FileContent,
    FileStorageProtocol,
    StoredFileNotFoundError,
)


class GetRecordAttachmentQueryHandler(_RecordLookup):
    def __init__(
        self,
        records: MedicalRecordRepositoryProtocol,
        access: DogAccess,
        storage: FileStorageProtocol,
    ):
        super().__init__(records, access)
        self._storage = storage

    async def handle(self, query: GetRecordAttachmentQuery) -> FileContent:
        record = await self._load(query.actor, query.dog_id, query.record_id)
        if not record.file_id:
            raise StoredFileNotFoundError()
        return await self._storage.load(record.file_id)
