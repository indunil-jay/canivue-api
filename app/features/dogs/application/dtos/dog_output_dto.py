from dataclasses import dataclass
from datetime import date, datetime

from app.features.dogs.domain.enums.dog_sex import DogSex
from app.features.dogs.domain.value_objects.insurance import Insurance
from app.features.dogs.domain.value_objects.medication import Medication
from app.features.dogs.domain.value_objects.vaccination import Vaccination


@dataclass(frozen=True)
class DogOutputDTO:
    id: str
    owner_id: int
    name: str
    breed: str
    birth_date: date
    gender: DogSex
    weight_kg: float
    color: str
    microchip_id: str
    avatar_emoji: str
    is_neutered: bool
    blood_group: str
    primary_vet: str
    special_notes: str
    allergies: list[str]
    existing_conditions: list[str]
    vaccinations: list[Vaccination]
    medications: list[Medication]
    insurance: Insurance | None
    photo_file_id: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime | None
    age_years: int
    age_months: int
    age_formatted: str
