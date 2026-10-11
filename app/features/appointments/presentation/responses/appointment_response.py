from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.veterinarians.domain.enums.consultation_type import ConsultationType


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
