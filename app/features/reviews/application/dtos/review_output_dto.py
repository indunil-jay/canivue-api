from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReviewOutputDTO:
    id: str
    appointment_id: str
    vet_id: str
    owner_id: int
    owner_name: str
    rating: int
    comment: str
    date: datetime
    created_at: datetime
    updated_at: datetime | None
