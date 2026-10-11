from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VetPatient:
    dog_id: str
    dog_name: str
    breed: str
    age_formatted: str
    owner_name: str
    last_visit: datetime | None
    needs_follow_up: bool
    has_critical_alert: bool
    allergies: list[str]
    existing_conditions: list[str]
    current_medications: list[str]
