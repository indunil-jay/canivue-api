from dataclasses import dataclass

from app.features.dashboard.domain.enums.insight_risk import InsightRisk


@dataclass(frozen=True)
class AiInsight:
    headline: str
    detail: str
    risk: InsightRisk = InsightRisk.NORMAL
