from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol

from app.core.exceptions import NotFoundException, ValidationException
from app.shared.entity import BaseEntity, _utc_now

SAFETY_NOTICE = (
    "This is a preliminary decision-support result and does not replace an examination "
    "by a licensed veterinarian."
)


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


class PredictionNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Prediction not found.")


class NoEvidenceError(ValidationException):
    def __init__(self) -> None:
        super().__init__(
            message="An Assessment needs a photo, a symptom description or recent collar data."
        )


# ---- What goes into the fusion engine -------------------------------------------------


@dataclass(frozen=True)
class DogFacts:
    name: str
    breed: str
    age_years: int
    allergies: tuple[str, ...] = ()
    special_notes: str = ""


@dataclass(frozen=True)
class SymptomEvidence:
    text: str
    symptoms: tuple[str, ...] = ()
    confidence: float = 0.0
    quality: float = 0.0
    worsening: bool = False
    emergency_reason: str | None = None
    emergency_recommendation: str | None = None


@dataclass(frozen=True)
class SensorEvidence:
    reading_count: int
    abnormal_fraction: float


@dataclass(frozen=True)
class FusionInput:
    dog: DogFacts
    has_image: bool = False
    symptoms: SymptomEvidence | None = None
    sensors: SensorEvidence | None = None


# ---- What comes out -------------------------------------------------------------------


@dataclass(frozen=True)
class ModalityResult:
    name: str
    available: bool
    confidence_percent: float
    quality_percent: float
    contribution_percent: float


@dataclass(frozen=True)
class FusionOutput:
    condition: str
    category: str
    final_confidence_percent: float
    severity_label: str
    modalities: list[ModalityResult]
    notes: list[str]


@dataclass(frozen=True)
class RiskFactor:
    label: str
    score_percent: float
    weight_percent: float
    contribution_points: float


@dataclass(frozen=True)
class ProgressionOutput:
    horizon_days: int
    risk_percent: float
    risk_level: RiskLevel
    factors: list[RiskFactor]
    main_reasons: list[str]
    recommendation: str
    missing_data_note: str | None = None


@dataclass(frozen=True)
class AssessmentResult:
    fusion: FusionOutput
    progression: ProgressionOutput
    model_version: str


class FusionEngineProtocol(Protocol):
    """Adaptive multimodal fusion plus seven-day progression risk for one Assessment."""

    async def assess(self, evidence: FusionInput) -> AssessmentResult: ...


@dataclass(frozen=True)
class ModelContribution:
    model_name: str
    contribution_percent: float


@dataclass
class Prediction(BaseEntity):
    dog_id: str = ""
    title: str = ""
    category: str = ""
    status: PredictionStatus = PredictionStatus.MONITORING
    combined_risk_percent: float = 0.0
    confidence_percent: float = 0.0
    prediction_date: datetime = field(default_factory=_utc_now)
    model_version: str = ""
    affected_indicators: list[str] = field(default_factory=list)
    recommended_next_step: str = ""
    model_contributions: list[ModelContribution] = field(default_factory=list)
    data_quality_note: str = ""
    historical_comparison_note: str = ""
    outcome_note: str | None = None
    image_file_id: str | None = None
    # The full Assessment (fusion and progression) as plain data, for the detail view.
    assessment: dict = field(default_factory=dict)


class PredictionRepositoryProtocol(Protocol):
    async def get_by_id(self, entity_id: str) -> Prediction | None: ...

    async def list_for_dog(self, dog_id: str) -> Sequence[Prediction]: ...

    async def latest_active(self, dog_id: str) -> Prediction | None: ...

    async def count_since(self, dog_ids: Sequence[str], since: datetime) -> int: ...

    async def create(self, entity: Prediction) -> Prediction: ...

    async def update(self, entity: Prediction) -> Prediction: ...
