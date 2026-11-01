from collections.abc import Sequence
from typing import Protocol

from app.features.dashboard.domain.value_objects.health_insight import HealthInsight
from app.features.dashboard.domain.value_objects.metric_trend import MetricTrend


class InsightEngineProtocol(Protocol):
    """Turns metric trends into plain-language statements for an owner."""

    async def summarise(
        self, dog_name: str, trends: Sequence[MetricTrend]
    ) -> list[HealthInsight]: ...
