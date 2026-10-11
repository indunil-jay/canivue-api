from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecentMessagePreviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: str
    owner_name: str
    preview: str
    sent_at: datetime
