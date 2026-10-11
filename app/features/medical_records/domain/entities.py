from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol

from app.core.exceptions import ForbiddenException, NotFoundException
from app.shared.entity import BaseEntity, _utc_now


class MedicalRecordType(str, Enum):
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION = "prescription"
    LAB_RESULT = "labResult"
    NOTE = "note"
    DOCUMENT = "document"


CLINICAL_TYPES = {
    MedicalRecordType.DIAGNOSIS,
    MedicalRecordType.PRESCRIPTION,
    MedicalRecordType.LAB_RESULT,
}


class MedicalRecordNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Medical record not found.")


class ClinicalRecordForbiddenError(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(
            message="Only a treating veterinarian can add a diagnosis, prescription or lab result."
        )


class NotRecordAuthorError(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(message="Only the author can delete a medical record.")


@dataclass
class MedicalRecord(BaseEntity):
    dog_id: str = ""
    type: MedicalRecordType = MedicalRecordType.NOTE
    title: str = ""
    description: str = ""
    date: datetime = field(default_factory=_utc_now)
    file_id: str | None = None
    author_user_id: int = 0
    author_name: str = ""
    authored_by_vet: bool = False


class MedicalRecordRepositoryProtocol(Protocol):
    async def get_by_id(self, entity_id: str) -> MedicalRecord | None: ...

    async def list_for_dog(self, dog_id: str) -> Sequence[MedicalRecord]: ...

    async def create(self, entity: MedicalRecord) -> MedicalRecord: ...

    async def delete(self, entity_id: str) -> bool: ...
