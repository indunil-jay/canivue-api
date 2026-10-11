from datetime import datetime

from pydantic import BaseModel, Field


class ReadingRequest(BaseModel):
    value: float
    recorded_at: datetime | None = Field(None, description="Defaults to now; UTC if no offset")
