from dataclasses import dataclass


@dataclass
class EmergencyTriageAlert:
    is_critical: bool = False
    reason: str | None = None
    recommendation: str | None = None
