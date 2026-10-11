from pydantic import BaseModel, Field

from app.features.health_metrics.presentation.requests.reading_request import ReadingRequest


class RecordReadingsRequest(BaseModel):
    readings: list[ReadingRequest] = Field(..., min_length=1, max_length=1000)
