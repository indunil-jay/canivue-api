from dataclasses import dataclass
from datetime import datetime

from app.features.medical_records.domain.enums.medical_record_type import MedicalRecordType


@dataclass(frozen=True)
class MedicalRecordOutputDTO:
    id: str
    dog_id: str
    type: MedicalRecordType
    title: str
    description: str
    date: datetime
    file_id: str | None
    author_user_id: int
    author_name: str
    authored_by_vet: bool
    created_at: datetime
    updated_at: datetime | None
