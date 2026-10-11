from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.features.dogs.domain.entities import DogSex, Insurance, Medication, Vaccination


class VaccinationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=100)
    date_given: date
    next_due_date: date | None = None


class MedicationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=100)
    dosage: str = Field("", max_length=100)
    frequency: str = Field("", max_length=100)


class InsuranceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str = Field(..., min_length=1, max_length=100)
    policy_number: str = Field(..., min_length=1, max_length=100)
    expiry_date: date


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


class DogCreateRequest(DogUpdateRequest):
    name: str = Field(..., min_length=1, max_length=100)
    breed: str = Field(..., max_length=100)
    birth_date: date
    gender: DogSex
    weight_kg: float = Field(..., gt=0, le=150)


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

    @classmethod
    def from_entity(cls, dog: Any) -> "DogResponse":
        response = cls.model_validate(dog)
        response.has_photo = dog.photo_file_id is not None
        return response
