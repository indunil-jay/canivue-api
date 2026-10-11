from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: float) -> "RiskLevel":
        if score >= 85:
            return cls.CRITICAL
        if score >= 60:
            return cls.HIGH
        if score >= 30:
            return cls.MODERATE
        return cls.LOW

    @property
    def recommendation(self) -> str:
        return {
            RiskLevel.LOW: "Continue routine at-home monitoring.",
            RiskLevel.MODERATE: "Schedule a routine vet check-up within 1-2 weeks.",
            RiskLevel.HIGH: "Veterinary consultation recommended within 24-48 hours.",
            RiskLevel.CRITICAL: "Seek urgent veterinary care as soon as possible.",
        }[self]
