from enum import Enum

from app.features.assessments.domain.enums.risk_level import RiskLevel


class PredictionStatus(str, Enum):
    MONITORING = "monitoring"
    LOW_RISK = "lowRisk"
    MODERATE_RISK = "moderateRisk"
    HIGH_RISK = "highRisk"
    RESOLVED = "resolved"
    VET_REVIEW_RECOMMENDED = "vetReviewRecommended"

    @classmethod
    def for_risk(cls, level: RiskLevel) -> "PredictionStatus":
        return {
            RiskLevel.LOW: cls.LOW_RISK,
            RiskLevel.MODERATE: cls.MODERATE_RISK,
            RiskLevel.HIGH: cls.HIGH_RISK,
            RiskLevel.CRITICAL: cls.VET_REVIEW_RECOMMENDED,
        }[level]
