from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScheduleEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    appointment_id: str
    time: datetime
    owner_name: str
    dog_name: str
    type: str
    confirmed: bool
