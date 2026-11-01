from dataclasses import dataclass
from datetime import datetime

from app.features.dashboard.domain.enums.timeline_event_type import TimelineEventType


@dataclass(frozen=True)
class HealthTimelineEvent:
    type: TimelineEventType
    title: str
    description: str
    date: datetime
