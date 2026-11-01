from pydantic import BaseModel


class ModalityResultSchema(BaseModel):
    name: str
    available: bool
    confidence_percent: float
    quality_percent: float
    contribution_percent: float
