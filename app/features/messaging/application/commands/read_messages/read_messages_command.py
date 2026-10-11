from dataclasses import dataclass
from datetime import datetime

from app.shared.actor import Actor


@dataclass(frozen=True)
class ReadMessagesCommand:
    actor: Actor
    conversation_id: str
    after: datetime | None = None
    limit: int = 200
