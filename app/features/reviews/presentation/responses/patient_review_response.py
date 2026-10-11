from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PatientReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    owner_name: str
    rating: int
    comment: str
    date: datetime
