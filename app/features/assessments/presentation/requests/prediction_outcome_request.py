from pydantic import BaseModel, Field


class PredictionOutcomeRequest(BaseModel):
    outcome_note: str = Field(..., min_length=1, max_length=2000)
    resolved: bool = False
