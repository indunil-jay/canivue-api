from pydantic import BaseModel, ConfigDict, Field

from app.features.reviews.presentation.responses.patient_review_response import (
    PatientReviewResponse,
)


class VetReputationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    average_rating: float
    total_consultations: int
    recommendations_accepted_percent: int = Field(..., description="Not tracked yet; always 0.")
    repeat_consultation_percent: int
    reviews: list[PatientReviewResponse]
