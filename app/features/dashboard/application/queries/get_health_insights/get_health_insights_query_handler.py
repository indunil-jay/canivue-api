from datetime import datetime, timedelta, timezone

from app.features.dashboard.application.dtos.dog_health_sources import DogHealthSources
from app.features.dashboard.application.interfaces.services.insight_engine import (
    InsightEngineProtocol,
)
from app.features.dashboard.application.queries.get_health_insights.get_health_insights_query import (
    GetHealthInsightsQuery,
)
from app.features.dashboard.domain.value_objects.health_insight import HealthInsight
from app.features.dashboard.domain.value_objects.metric_trend import MetricTrend
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.health_metrics.domain.constants import CUMULATIVE
from app.features.health_metrics.domain.enums.health_metric import HealthMetric


class GetHealthInsightsQueryHandler:
    def __init__(self, sources: DogHealthSources, access: DogAccess, engine: InsightEngineProtocol):
        self._s = sources
        self._access = access
        self._engine = engine

    async def handle(self, query: GetHealthInsightsQuery) -> list[HealthInsight]:
        dog = await self._access.readable(query.actor, query.dog_id)
        now = datetime.now(timezone.utc)
        boundary = now - timedelta(days=30)
        trends = []
        for metric in HealthMetric:
            readings = await self._s.readings.list_since(dog.id, metric, now - timedelta(days=60))
            recent = [r for r in readings if r.recorded_at >= boundary]
            previous = [r for r in readings if r.recorded_at < boundary]
            if recent and previous:
                trends.append(
                    MetricTrend(
                        metric, _daily_average(metric, recent), _daily_average(metric, previous)
                    )
                )
        return await self._engine.summarise(dog.name, trends)


def _daily_average(metric: HealthMetric, readings: list) -> float:
    """Average per day: cumulative metrics are totalled within a day first."""
    by_day: dict = {}
    for r in readings:
        by_day.setdefault(r.recorded_at.date(), []).append(r.value)
    combine = sum if metric in CUMULATIVE else (lambda values: sum(values) / len(values))
    daily = [combine(values) for values in by_day.values()]
    return sum(daily) / len(daily)
