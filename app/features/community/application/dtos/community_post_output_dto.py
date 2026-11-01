from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CommunityPostOutputDTO:
    id: str
    author_id: int
    author_name: str
    is_veterinarian: bool
    community_id: str
    community_tag: str
    content: str
    share_count: int
    created_at: datetime
    updated_at: datetime | None
