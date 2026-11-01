from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    appointment_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field("", max_length=2000)
