from typing import Any

from pydantic import BaseModel, Field

from app.features.veterinarians.application.use_cases import VeterinarianView
from app.features.veterinarians.domain.entities import ConsultationType
from app.shared.text import initials_of


class VetProfileUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    specialty: str | None = Field(None, max_length=100)
    specialties: list[str] | None = None
    experience_years: int | None = Field(None, ge=0, le=80)
    consultation_fee_usd: float | None = Field(None, ge=0, le=10_000)
    response_time_minutes: int | None = Field(None, ge=0, le=10_080)
    languages: list[str] | None = None
    consultation_types: list[ConsultationType] | None = None
    bio: str | None = Field(None, max_length=4000)
    clinics: list[str] | None = None
    qualifications: list[str] | None = None

    def to_domain(self) -> dict[str, Any]:
        data = self.model_dump(exclude_none=True)
        if "consultation_types" in data:
            data["consultation_types"] = [t.value for t in data["consultation_types"]]
        return data


class SetAvailabilityRequest(BaseModel):
    available: bool


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

    @classmethod
    def from_view(cls, view: VeterinarianView) -> "VeterinarianResponse":
        p, s = view.profile, view.stats
        return cls(
            id=p.id,
            name=p.name,
            initials=initials_of(p.name),
            verified=p.verified,
            specialty=p.specialty,
            specialties=p.specialties,
            experience_years=p.experience_years,
            rating=s.rating,
            review_count=s.review_count,
            consultation_count=s.consultation_count,
            response_time_minutes=p.response_time_minutes,
            consultation_fee_usd=p.consultation_fee_usd,
            languages=p.languages,
            available_today=view.available_today,
            consultation_types=p.consultation_types,
            bio=p.bio,
            clinics=p.clinics,
            qualifications=p.qualifications,
            follow_up_rate_percent=s.follow_up_rate_percent,
            recommendations_accepted_percent=s.recommendations_accepted_percent,
        )
