from datetime import datetime

from pydantic import BaseModel

from app.features.medical_records.domain.enums.medical_record_type import MedicalRecordType


class MedicalRecordResponse(BaseModel):
    id: str
    dog_id: str
    type: MedicalRecordType
    title: str
    description: str
    date: datetime
    attachment_url: str | None
    author_name: str
    authored_by_vet: bool
