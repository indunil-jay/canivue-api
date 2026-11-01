from dataclasses import dataclass, field
from datetime import datetime

from app.shared.entity import BaseEntity, _utc_now


@dataclass
class Review(BaseEntity):
    appointment_id: str = ""
    vet_id: str = ""
    owner_id: int = 0
    owner_name: str = ""
    rating: int = 5
    comment: str = ""
    date: datetime = field(default_factory=_utc_now)
