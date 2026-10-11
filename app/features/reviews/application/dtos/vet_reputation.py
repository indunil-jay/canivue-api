from dataclasses import dataclass

from app.features.reviews.application.dtos.review_output_dto import ReviewOutputDTO


@dataclass(frozen=True)
class VetReputation:
    average_rating: float
    total_consultations: int
    recommendations_accepted_percent: int
    repeat_consultation_percent: int
    reviews: list[ReviewOutputDTO]
