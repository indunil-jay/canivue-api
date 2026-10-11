from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.appointments.domain.entities import AppointmentStatus
from app.features.veterinarians.domain.entities import ConsultationType


class BookAppointmentRequest(BaseModel):
    vet_id: str
    date_time: datetime = Field(..., description="ISO 8601; a value without an offset is UTC")
    consultation_type: ConsultationType
    notes: str = Field("", max_length=2000)


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    vet_id: str
    vet_name: str
    dog_id: str
    dog_name: str
    owner_name: str
    date_time: datetime
    status: AppointmentStatus
    consultation_type: ConsultationType
    fee_usd: float
    notes: str
