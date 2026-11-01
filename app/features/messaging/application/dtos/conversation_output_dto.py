from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConversationOutputDTO:
    id: str
    owner_id: int
    owner_name: str
    vet_id: str
    vet_user_id: int
    vet_name: str
    last_message_preview: str
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
