from dataclasses import dataclass

from app.features.dashboard.domain.enums.trend_direction import TrendDirection


@dataclass(frozen=True)
class HealthInsight:
    headline: str
    detail: str
    direction: TrendDirection
    is_positive: bool = True
