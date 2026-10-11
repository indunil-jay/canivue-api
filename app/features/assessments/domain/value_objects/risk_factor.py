from dataclasses import dataclass


@dataclass(frozen=True)
class RiskFactor:
    label: str
    score_percent: float
    weight_percent: float
    contribution_points: float
