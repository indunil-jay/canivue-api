from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UpcomingAppointment:
    vet_name: str
    clinic: str
    time: datetime
    is_video_call: bool
