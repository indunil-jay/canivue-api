from dataclasses import dataclass
from datetime import datetime

from app.features.medical_records.domain.enums.medical_record_type import MedicalRecordType


@dataclass(frozen=True)
class NewRecordInput:
    type: MedicalRecordType
    title: str
    description: str = ""
    date: datetime | None = None
