from dataclasses import dataclass


@dataclass(frozen=True)
class VetStats:
    rating: float = 0.0
    review_count: int = 0
    consultation_count: int = 0
    follow_up_rate_percent: int = 0
    recommendations_accepted_percent: int = 0
