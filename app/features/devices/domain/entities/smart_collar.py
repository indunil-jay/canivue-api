from dataclasses import dataclass, field
from datetime import datetime

from app.features.devices.domain.constants import (
    DEFAULT_NAME,
    DEFAULT_PERMISSIONS,
    SYNC_HISTORY_LIMIT,
)
from app.features.devices.domain.enums.collar_connection_state import CollarConnectionState
from app.features.devices.domain.exceptions import CollarNotConnectedError, CollarNotPairedError
from app.features.devices.domain.value_objects.sync_event import SyncEvent
from app.shared.entity import BaseEntity, _utc_now


@dataclass
class SmartCollar(BaseEntity):
    dog_id: str = ""
    name: str = DEFAULT_NAME
    state: CollarConnectionState = CollarConnectionState.NOT_PAIRED
    battery_percent: int | None = None
    last_synced_at: datetime | None = None
    firmware_version: str = ""
    sync_history: list[SyncEvent] = field(default_factory=list)
    granted_permissions: list[str] = field(default_factory=lambda: list(DEFAULT_PERMISSIONS))

    @property
    def is_paired(self) -> bool:
        return self.state != CollarConnectionState.NOT_PAIRED

    def pair(self) -> None:
        self.state = CollarConnectionState.CONNECTED
        self.updated_at = _utc_now()

    def disconnect(self) -> None:
        if not self.is_paired:
            raise CollarNotPairedError()
        self.state = CollarConnectionState.DISCONNECTED
        self.updated_at = _utc_now()

    def rename(self, name: str) -> None:
        if not self.is_paired:
            raise CollarNotPairedError()
        self.name = name.strip()
        self.updated_at = _utc_now()

    def record_sync(self, records_synced: int, battery_percent: int | None) -> None:
        if self.state != CollarConnectionState.CONNECTED:
            raise CollarNotConnectedError("sync")
        now = _utc_now()
        self.last_synced_at = now
        if battery_percent is not None:
            self.battery_percent = battery_percent
        self.sync_history = [SyncEvent(now, records_synced), *self.sync_history][
            :SYNC_HISTORY_LIMIT
        ]
        self.updated_at = now
