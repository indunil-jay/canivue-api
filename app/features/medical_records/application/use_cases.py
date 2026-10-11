from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.features.dogs.application.access import DogAccess
from app.features.medical_records.domain.entities import (
    CLINICAL_TYPES,
    ClinicalRecordForbiddenError,
    MedicalRecord,
    MedicalRecordNotFoundError,
    MedicalRecordRepositoryProtocol,
    MedicalRecordType,
    NotRecordAuthorError,
)
from app.shared.actor import Actor
from app.shared.entity import _utc_now
from app.shared.files import (
    DOCUMENT_TYPES,
    FileContent,
    FileStorageProtocol,
    StoredFileNotFoundError,
    validate_upload,
)


@dataclass(frozen=True)
class NewRecordInput:
    type: MedicalRecordType
    title: str
    description: str = ""
    date: datetime | None = None


class ListMedicalRecordsUseCase:
    def __init__(self, records: MedicalRecordRepositoryProtocol, access: DogAccess):
        self._records = records
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> Sequence[MedicalRecord]:
        dog = await self._access.readable(actor, dog_id)
        return await self._records.list_for_dog(dog.id)


class AddMedicalRecordUseCase:
    def __init__(self, records: MedicalRecordRepositoryProtocol, access: DogAccess):
        self._records = records
        self._access = access

    async def execute(self, actor: Actor, dog_id: str, data: NewRecordInput) -> MedicalRecord:
        dog = await self._access.readable(actor, dog_id)
        treating = dog.owner_id != actor.id and (actor.is_vet or actor.is_admin)
        if data.type in CLINICAL_TYPES and not treating:
            raise ClinicalRecordForbiddenError()
        return await self._records.create(
            MedicalRecord(
                dog_id=dog.id,
                type=data.type,
                title=data.title.strip(),
                description=data.description.strip(),
                date=data.date or _utc_now(),
                author_user_id=actor.id,
                author_name=actor.display_name,
                authored_by_vet=treating and actor.is_vet,
            )
        )


class UploadMedicalDocumentUseCase:
    def __init__(
        self,
        records: MedicalRecordRepositoryProtocol,
        access: DogAccess,
        storage: FileStorageProtocol,
    ):
        self._records = records
        self._access = access
        self._storage = storage

    async def execute(
        self,
        actor: Actor,
        dog_id: str,
        title: str,
        content: bytes,
        content_type: str | None,
        max_bytes: int,
    ) -> MedicalRecord:
        dog = await self._access.readable(actor, dog_id)
        accepted_type = validate_upload(content, content_type, DOCUMENT_TYPES, max_bytes)
        file_id = await self._storage.save(content, accepted_type)
        return await self._records.create(
            MedicalRecord(
                dog_id=dog.id,
                type=MedicalRecordType.DOCUMENT,
                title=title.strip(),
                description="Uploaded document",
                file_id=file_id,
                author_user_id=actor.id,
                author_name=actor.display_name,
                authored_by_vet=actor.is_vet and dog.owner_id != actor.id,
            )
        )


class _RecordLookup:
    def __init__(self, records: MedicalRecordRepositoryProtocol, access: DogAccess):
        self._records = records
        self._access = access

    async def _load(self, actor: Actor, dog_id: str, record_id: str) -> MedicalRecord:
        dog = await self._access.readable(actor, dog_id)
        record = await self._records.get_by_id(record_id)
        if record is None or record.dog_id != dog.id:
            raise MedicalRecordNotFoundError()
        return record


class GetRecordAttachmentUseCase(_RecordLookup):
    def __init__(
        self,
        records: MedicalRecordRepositoryProtocol,
        access: DogAccess,
        storage: FileStorageProtocol,
    ):
        super().__init__(records, access)
        self._storage = storage

    async def execute(self, actor: Actor, dog_id: str, record_id: str) -> FileContent:
        record = await self._load(actor, dog_id, record_id)
        if not record.file_id:
            raise StoredFileNotFoundError()
        return await self._storage.load(record.file_id)


class DeleteMedicalRecordUseCase(_RecordLookup):
    def __init__(
        self,
        records: MedicalRecordRepositoryProtocol,
        access: DogAccess,
        storage: FileStorageProtocol,
    ):
        super().__init__(records, access)
        self._storage = storage

    async def execute(self, actor: Actor, dog_id: str, record_id: str) -> None:
        record = await self._load(actor, dog_id, record_id)
        if record.author_user_id != actor.id and not actor.is_admin:
            raise NotRecordAuthorError()
        await self._records.delete(record.id)
        if record.file_id:
            await self._storage.delete(record.file_id)
