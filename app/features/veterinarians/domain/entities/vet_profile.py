from dataclasses import dataclass, field
from datetime import datetime

from app.features.veterinarians.domain.constants import WEEKDAYS
from app.features.veterinarians.domain.enums.consultation_type import ConsultationType
from app.features.veterinarians.domain.services.default_availability import default_availability
from app.shared.entity import BaseEntity


@dataclass
class VetProfile(BaseEntity):
    user_id: int = 0
    name: str = ""
    verified: bool = False
    specialty: str = "General Practice"
    specialties: list[str] = field(default_factory=list)
    experience_years: int = 0
    consultation_fee_usd: float = 0.0
    response_time_minutes: int = 60
    languages: list[str] = field(default_factory=lambda: ["English"])
    consultation_types: list[str] = field(
        default_factory=lambda: [t.value for t in ConsultationType]
    )
    bio: str = ""
    clinics: list[str] = field(default_factory=list)
    qualifications: list[str] = field(default_factory=list)
    availability: dict[str, bool] = field(default_factory=default_availability)

    def is_available_on(self, moment: datetime) -> bool:
        return self.availability.get(WEEKDAYS[moment.weekday()], False)

    def offers(self, consultation_type: ConsultationType) -> bool:
        return consultation_type.value in self.consultation_types

    def matches(self, query: str) -> bool:
        needle = query.strip().lower()
        haystack = [self.name, self.specialty, *self.specialties]
        return not needle or any(needle in text.lower() for text in haystack)

    def has_specialty(self, specialty: str) -> bool:
        wanted = specialty.strip().lower()
        return wanted in {self.specialty.lower(), *(s.lower() for s in self.specialties)}
