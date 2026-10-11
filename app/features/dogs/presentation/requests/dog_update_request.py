from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.features.dogs.domain.enums.dog_sex import DogSex
from app.features.dogs.domain.value_objects.insurance import Insurance
from app.features.dogs.domain.value_objects.medication import Medication
from app.features.dogs.domain.value_objects.vaccination import Vaccination
from app.features.dogs.presentation.schemas.insurance_schema import InsuranceSchema
from app.features.dogs.presentation.schemas.medication_schema import MedicationSchema
from app.features.dogs.presentation.schemas.vaccination_schema import VaccinationSchema


class DogUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    breed: str | None = Field(None, max_length=100)
    birth_date: date | None = None
    gender: DogSex | None = None
    weight_kg: float | None = Field(None, gt=0, le=150)
    color: str | None = Field(None, max_length=100)
    microchip_id: str | None = Field(None, max_length=50)
    avatar_emoji: str | None = Field(None, max_length=16)
    is_neutered: bool | None = None
    blood_group: str | None = Field(None, max_length=30)
    primary_vet: str | None = Field(None, max_length=255)
    special_notes: str | None = Field(None, max_length=2000)
    allergies: list[str] | None = None
    existing_conditions: list[str] | None = None
    vaccinations: list[VaccinationSchema] | None = None
    medications: list[MedicationSchema] | None = None
    insurance: InsuranceSchema | None = None

    def to_domain(self) -> dict[str, Any]:
        # Only fields the client actually sent; an explicit null clears insurance.
        data: dict[str, Any] = {
            name: getattr(self, name)
            for name in self.model_fields_set
            if getattr(self, name) is not None or name == "insurance"
        }
        if "vaccinations" in data:
            data["vaccinations"] = [Vaccination(**v.model_dump()) for v in data["vaccinations"]]
        if "medications" in data:
            data["medications"] = [Medication(**m.model_dump()) for m in data["medications"]]
        if data.get("insurance") is not None:
            data["insurance"] = Insurance(**data["insurance"].model_dump())
        return data
