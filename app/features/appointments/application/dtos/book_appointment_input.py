from dataclasses import dataclass
from datetime import datetime

from app.features.veterinarians.domain.enums.consultation_type import ConsultationType


@dataclass(frozen=True)
class BookAppointmentInput:
    dog_id: str
    vet_id: str
    date_time: datetime
    consultation_type: ConsultationType
    notes: str = ""
