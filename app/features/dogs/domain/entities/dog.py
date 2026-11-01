from dataclasses import dataclass, field
from datetime import date

from app.features.dogs.domain.enums.dog_sex import DogSex
from app.features.dogs.domain.value_objects.insurance import Insurance
from app.features.dogs.domain.value_objects.medication import Medication
from app.features.dogs.domain.value_objects.vaccination import Vaccination
from app.shared.entity import BaseEntity


@dataclass
class Dog(BaseEntity):
    owner_id: int = 0
    name: str = ""
    breed: str = ""
    birth_date: date = field(default_factory=date.today)
    gender: DogSex = DogSex.MALE
    weight_kg: float = 0.0
    color: str = ""
    microchip_id: str = ""
    avatar_emoji: str = "🐶"
    is_neutered: bool = False
    blood_group: str = ""
    primary_vet: str = ""
    special_notes: str = ""
    allergies: list[str] = field(default_factory=list)
    existing_conditions: list[str] = field(default_factory=list)
    vaccinations: list[Vaccination] = field(default_factory=list)
    medications: list[Medication] = field(default_factory=list)
    insurance: Insurance | None = None
    photo_file_id: str | None = None
    is_archived: bool = False

    def _age_in_months(self) -> int:
        today = date.today()
        months = (today.year - self.birth_date.year) * 12 + today.month - self.birth_date.month
        if today.day < self.birth_date.day:
            months -= 1
        return max(months, 0)

    @property
    def age_years(self) -> int:
        return self._age_in_months() // 12

    @property
    def age_months(self) -> int:
        return self._age_in_months() % 12

    @property
    def age_formatted(self) -> str:
        years, months = self.age_years, self.age_months
        if years and months:
            return f"{years} yrs {months} mos"
        return f"{years} yrs" if years else f"{months} mos"
