from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DiseaseCommunityOutputDTO:
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime | None
