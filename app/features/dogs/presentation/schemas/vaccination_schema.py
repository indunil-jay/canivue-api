from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class VaccinationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=100)
    date_given: date
    next_due_date: date | None = None
