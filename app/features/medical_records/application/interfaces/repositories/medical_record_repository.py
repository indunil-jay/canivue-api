from collections.abc import Sequence
from typing import Protocol

from app.features.medical_records.domain.entities.medical_record import MedicalRecord


class MedicalRecordRepositoryProtocol(Protocol):
    async def get_by_id(self, entity_id: str) -> MedicalRecord | None: ...

    async def list_for_dog(self, dog_id: str) -> Sequence[MedicalRecord]: ...

    async def create(self, entity: MedicalRecord) -> MedicalRecord: ...

    async def delete(self, entity_id: str) -> bool: ...
