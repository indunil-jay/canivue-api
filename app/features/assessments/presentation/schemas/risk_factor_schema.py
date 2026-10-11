from pydantic import BaseModel


class RiskFactorSchema(BaseModel):
    label: str
    score_percent: float
    weight_percent: float
    contribution_points: float
