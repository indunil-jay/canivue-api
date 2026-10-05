from dataclasses import dataclass, field


@dataclass
class BodyLocation:
    part: str
    side: str | None = None


@dataclass
class DurationEntity:
    value: int
    unit: str


@dataclass
class ExtractedSpan:
    entity: str
    text: str
    start: int
    end: int
    negated: bool = False


@dataclass
class EmergencyTriageAlert:
    is_critical: bool = False
    reason: str | None = None
    recommendation: str | None = None


@dataclass
class ConditionProbability:
    condition: str
    probability: float


@dataclass
class SymptomParseResult:
    raw_text: str
    symptoms: list[str] = field(default_factory=list)
    negated_symptoms: list[str] = field(default_factory=list)
    body_locations: list[BodyLocation] = field(default_factory=list)
    duration: DurationEntity | None = None
    frequency: dict[str, str] | None = None
    severity_cues: list[str] = field(default_factory=list)
    new_symptoms: list[str] = field(default_factory=list)
    progression: str | None = None
    behaviours: list[str] = field(default_factory=list)
    condition_probabilities: dict[str, float] = field(default_factory=dict)
    spans: list[ExtractedSpan] = field(default_factory=list)
    text_quality_score: float = 0.0
    model_confidence: float = 0.0
    modality_reliability_score: float = 0.0
    emergency_triage: EmergencyTriageAlert = field(default_factory=EmergencyTriageAlert)
    warnings: list[str] = field(default_factory=list)
    model_version: str = "stub_nlp_engine_v1"
