from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RecentMessagePreview:
    conversation_id: str
    owner_name: str
    preview: str
    sent_at: datetime
