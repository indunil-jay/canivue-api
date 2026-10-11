from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SyncEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    records_synced: int
