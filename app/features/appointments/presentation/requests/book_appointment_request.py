from datetime import datetime

from pydantic import BaseModel, Field

from app.features.veterinarians.domain.enums.consultation_type import ConsultationType


class BookAppointmentRequest(BaseModel):
    vet_id: str
    date_time: datetime = Field(..., description="ISO 8601; a value without an offset is UTC")
    consultation_type: ConsultationType
    notes: str = Field("", max_length=2000)
