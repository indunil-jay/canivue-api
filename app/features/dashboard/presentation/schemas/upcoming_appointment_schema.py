from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UpcomingAppointmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vet_name: str
    clinic: str
    time: datetime
    is_video_call: bool
