from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VetPatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
