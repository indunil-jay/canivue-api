from dataclasses import dataclass
from datetime import datetime

from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.veterinarians.domain.enums.consultation_type import ConsultationType


@dataclass(frozen=True)
class AppointmentOutputDTO:
    id: str
    owner_id: int
    owner_name: str
    vet_id: str
    vet_user_id: int
    vet_name: str
    dog_id: str
    dog_name: str
    date_time: datetime
    status: AppointmentStatus
    consultation_type: ConsultationType
    fee_usd: float
    notes: str
    created_at: datetime
    updated_at: datetime | None
