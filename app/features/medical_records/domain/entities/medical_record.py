from dataclasses import dataclass, field
from datetime import datetime

from app.features.medical_records.domain.enums.medical_record_type import MedicalRecordType
from app.shared.entity import BaseEntity, _utc_now


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
