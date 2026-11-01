from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VetProfileOutputDTO:
    id: str
    user_id: int
    name: str
    verified: bool
    specialty: str
    specialties: list[str]
    experience_years: int
    consultation_fee_usd: float
    response_time_minutes: int
    languages: list[str]
    consultation_types: list[str]
    bio: str
    clinics: list[str]
    qualifications: list[str]
    availability: dict[str, bool]
    created_at: datetime
    updated_at: datetime | None
