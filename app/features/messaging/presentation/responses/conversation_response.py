from datetime import datetime

from pydantic import BaseModel, Field


class ConversationResponse(BaseModel):
    id: str
    vet_id: str
    vet_name: str
    vet_initials: str
    owner_name: str
    last_message_preview: str
    last_message_at: datetime | None
    unread_count: int
    online: bool = Field(False, description="Presence is not tracked yet; always false.")
