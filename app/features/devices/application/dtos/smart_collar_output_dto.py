from dataclasses import dataclass
from datetime import datetime

from app.features.devices.domain.enums.collar_connection_state import CollarConnectionState
from app.features.devices.domain.value_objects.sync_event import SyncEvent


@dataclass(frozen=True)
class SmartCollarOutputDTO:
    id: str
    dog_id: str
    name: str
    state: CollarConnectionState
    battery_percent: int | None
    last_synced_at: datetime | None
    firmware_version: str
    sync_history: list[SyncEvent]
    granted_permissions: list[str]
    created_at: datetime
    updated_at: datetime | None
    is_paired: bool
