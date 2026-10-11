from pydantic import BaseModel, ConfigDict

from app.features.dashboard.domain.enums.trend_direction import TrendDirection


class HealthInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    headline: str
    detail: str
    direction: TrendDirection
    is_positive: bool
