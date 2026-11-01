from pydantic import BaseModel, Field


class SyncCollarRequest(BaseModel):
    records_synced: int = Field(0, ge=0)
    battery_percent: int | None = Field(None, ge=0, le=100)
