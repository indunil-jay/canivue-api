from dataclasses import dataclass

from app.features.veterinarians.domain.enums.consultation_type import ConsultationType


@dataclass(frozen=True)
class VetSearchFilters:
    query: str = ""
    specialty: str | None = None
    consultation_type: ConsultationType | None = None
    available_today_only: bool = False
