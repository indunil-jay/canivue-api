from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.features.dogs.domain.enums.dog_sex import DogSex
from app.features.dogs.presentation.schemas.insurance_schema import InsuranceSchema
from app.features.dogs.presentation.schemas.medication_schema import MedicationSchema
from app.features.dogs.presentation.schemas.vaccination_schema import VaccinationSchema


class DogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    breed: str
    birth_date: date
    age_years: int
    age_months: int
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
    vaccinations: list[VaccinationSchema]
    medications: list[MedicationSchema]
    insurance: InsuranceSchema | None
    has_photo: bool = False
    created_at: datetime
