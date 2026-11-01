from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.devices.domain.enums.collar_connection_state import CollarConnectionState
from app.features.devices.presentation.responses.sync_event_response import SyncEventResponse


class SmartCollarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dog_id: str
    name: str
    state: CollarConnectionState
    battery_percent: int | None
    last_synced_at: datetime | None
    firmware_version: str
    sync_history: list[SyncEventResponse]
    granted_permissions: list[str]
