from dataclasses import dataclass
from datetime import datetime

from app.features.dashboard.domain.enums.device_connection_state import DeviceConnectionState


@dataclass(frozen=True)
class DeviceStatus:
    state: DeviceConnectionState
    device_name: str
    battery_percent: int | None
    last_synced_at: datetime | None
