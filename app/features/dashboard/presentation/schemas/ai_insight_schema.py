from pydantic import BaseModel, ConfigDict

from app.features.dashboard.domain.enums.insight_risk import InsightRisk


class AiInsightSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    headline: str
    detail: str
    risk: InsightRisk
