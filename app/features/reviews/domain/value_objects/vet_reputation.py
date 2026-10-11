from collections.abc import Sequence
from dataclasses import dataclass

from app.features.reviews.domain.entities.review import Review


@dataclass(frozen=True)
class VetReputation:
    average_rating: float
    total_consultations: int
    recommendations_accepted_percent: int
    repeat_consultation_percent: int
    reviews: Sequence[Review]
