from pydantic import BaseModel, ConfigDict, Field


class MedicationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=100)
    dosage: str = Field("", max_length=100)
    frequency: str = Field("", max_length=100)
