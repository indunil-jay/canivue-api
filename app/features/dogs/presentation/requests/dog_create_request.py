from datetime import date

from pydantic import Field

from app.features.dogs.domain.enums.dog_sex import DogSex
from app.features.dogs.presentation.requests.dog_update_request import DogUpdateRequest


class DogCreateRequest(DogUpdateRequest):
    name: str = Field(..., min_length=1, max_length=100)
    breed: str = Field(..., max_length=100)
    birth_date: date
    gender: DogSex
    weight_kg: float = Field(..., gt=0, le=150)
