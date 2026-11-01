from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SyncEvent:
    timestamp: datetime
    records_synced: int
