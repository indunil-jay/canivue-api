from dataclasses import dataclass


@dataclass(frozen=True)
class SymptomEvidence:
    text: str
    symptoms: tuple[str, ...] = ()
    confidence: float = 0.0
    quality: float = 0.0
    worsening: bool = False
    emergency_reason: str | None = None
    emergency_recommendation: str | None = None
