from pydantic import BaseModel


class EmergencyTriageSchema(BaseModel):
    is_critical: bool = False
    reason: str | None = None
    recommendation: str | None = None
