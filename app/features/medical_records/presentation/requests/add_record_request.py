from datetime import datetime

from pydantic import BaseModel, Field

from app.features.medical_records.domain.enums.medical_record_type import MedicalRecordType


class AddRecordRequest(BaseModel):
    type: MedicalRecordType
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field("", max_length=8000)
    date: datetime | None = None
