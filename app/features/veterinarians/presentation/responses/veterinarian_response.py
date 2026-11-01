from pydantic import BaseModel, Field

from app.features.veterinarians.domain.enums.consultation_type import ConsultationType


class VeterinarianResponse(BaseModel):
    id: str
    name: str
    initials: str
    verified: bool
    specialty: str
    specialties: list[str]
    experience_years: int
    rating: float
    review_count: int
    consultation_count: int
    response_time_minutes: int
    consultation_fee_usd: float
    languages: list[str]
    distance_km: float | None = Field(None, description="Not computed yet; always null.")
    available_today: bool
    consultation_types: list[ConsultationType]
    bio: str
    clinics: list[str]
    qualifications: list[str]
    follow_up_rate_percent: int
    recommendations_accepted_percent: int
