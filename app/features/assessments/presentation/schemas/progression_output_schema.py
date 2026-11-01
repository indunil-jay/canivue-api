from pydantic import BaseModel

from app.features.assessments.domain.enums.risk_level import RiskLevel
from app.features.assessments.presentation.schemas.risk_factor_schema import RiskFactorSchema


class ProgressionOutputSchema(BaseModel):
    horizon_days: int
    risk_percent: float
    risk_level: RiskLevel
    factors: list[RiskFactorSchema]
    main_reasons: list[str]
    recommendation: str
    missing_data_note: str | None
