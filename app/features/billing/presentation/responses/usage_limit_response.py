from pydantic import BaseModel, ConfigDict, Field


class UsageLimitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    used: int
    limit: int = Field(..., description="-1 means unlimited")
