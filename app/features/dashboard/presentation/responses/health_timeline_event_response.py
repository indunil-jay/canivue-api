from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.dashboard.domain.enums.timeline_event_type import TimelineEventType


class HealthTimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: TimelineEventType
    title: str
    description: str
    date: datetime
