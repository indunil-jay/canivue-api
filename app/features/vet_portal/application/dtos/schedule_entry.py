from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ScheduleEntry:
    appointment_id: str
    time: datetime
    owner_name: str
    dog_name: str
    type: str
    confirmed: bool
