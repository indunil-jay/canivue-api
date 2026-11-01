from dataclasses import dataclass

from app.features.assessments.domain.enums.risk_level import RiskLevel
from app.features.assessments.domain.value_objects.risk_factor import RiskFactor


@dataclass(frozen=True)
class ProgressionOutput:
    horizon_days: int
    risk_percent: float
    risk_level: RiskLevel
    factors: list[RiskFactor]
    main_reasons: list[str]
    recommendation: str
    missing_data_note: str | None = None
