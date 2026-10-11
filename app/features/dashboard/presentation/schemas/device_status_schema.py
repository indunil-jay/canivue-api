from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.dashboard.domain.enums.device_connection_state import DeviceConnectionState


class DeviceStatusSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    state: DeviceConnectionState
    device_name: str
    battery_percent: int | None
    last_synced_at: datetime | None
