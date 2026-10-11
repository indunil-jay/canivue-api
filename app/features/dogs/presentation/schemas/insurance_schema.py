from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class InsuranceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str = Field(..., min_length=1, max_length=100)
    policy_number: str = Field(..., min_length=1, max_length=100)
    expiry_date: date
