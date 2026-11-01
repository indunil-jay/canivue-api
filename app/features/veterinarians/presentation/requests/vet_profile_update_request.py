from typing import Any

from pydantic import BaseModel, Field

from app.features.veterinarians.domain.enums.consultation_type import ConsultationType


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
