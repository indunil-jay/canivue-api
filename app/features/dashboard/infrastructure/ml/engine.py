from collections.abc import Sequence

from app.features.dashboard.application.interfaces.services.insight_engine import (
    InsightEngineProtocol,
)
from app.features.dashboard.domain.enums.trend_direction import TrendDirection
from app.features.dashboard.domain.value_objects.health_insight import HealthInsight
from app.features.dashboard.domain.value_objects.metric_trend import MetricTrend
from app.features.health_metrics.domain.enums.health_metric import HealthMetric

STABLE_BAND_PERCENT = 5.0

# (label, whether a rise is good news, whether a fall is good news)
_READING = {
    HealthMetric.ACTIVITY: ("Activity", True, False),
    HealthMetric.SLEEP: ("Sleep", True, False),
    HealthMetric.HYDRATION: ("Hydration", True, False),
    HealthMetric.HEART_RATE: ("Resting heart rate", False, True),
    HealthMetric.WEIGHT: ("Weight", False, False),
    HealthMetric.TEMPERATURE: ("Body temperature", False, False),
}


class StubInsightEngine(InsightEngineProtocol):
    """Rule-based stand-in for the long-term insight model: month-on-month change per metric."""

    async def summarise(self, dog_name: str, trends: Sequence[MetricTrend]) -> list[HealthInsight]:
        insights = []
        for trend in trends:
            label, rise_is_good, fall_is_good = _READING[trend.metric]
            change = trend.change_percent
            if abs(change) < STABLE_BAND_PERCENT:
                insights.append(
                    HealthInsight(
                        headline=f"{label} is steady",
                        detail=f"{dog_name}'s {label.lower()} is within {STABLE_BAND_PERCENT:.0f}% "
                        "of last month.",
                        direction=TrendDirection.STABLE,
                        is_positive=True,
                    )
                )
                continue
            rose = change > 0
            verb = "increased" if rose else "decreased"
            positive = rise_is_good if rose else fall_is_good
            insights.append(
                HealthInsight(
                    headline=f"{label} {verb} {abs(change):.0f}% this month",
                    detail=(
                        f"{dog_name}'s {label.lower()} averaged {trend.recent_average:.1f} over "
                        f"the last 30 days, against {trend.previous_average:.1f} the month before."
                        + ("" if positive else " Worth keeping an eye on.")
                    ),
                    direction=TrendDirection.UP if rose else TrendDirection.DOWN,
                    is_positive=positive,
                )
            )
        return insights
