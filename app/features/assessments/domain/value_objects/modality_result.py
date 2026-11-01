from dataclasses import dataclass


@dataclass(frozen=True)
class ModalityResult:
    name: str
    available: bool
    confidence_percent: float
    quality_percent: float
    contribution_percent: float
