from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.features.assessments.domain.entities import (
    AssessmentResult,
    DogFacts,
    FusionEngineProtocol,
    FusionInput,
    ModelContribution,
    NoEvidenceError,
    Prediction,
    PredictionNotFoundError,
    PredictionRepositoryProtocol,
    PredictionStatus,
    RiskLevel,
    SensorEvidence,
    SymptomEvidence,
)
from app.features.dogs.application.access import DogAccess
from app.features.dogs.domain.entities import Dog
from app.features.health_metrics.domain.entities import (
    HealthMetric,
    MetricReadingRepositoryProtocol,
    MetricTimeRange,
    build_series,
    history_start,
)
from app.shared.actor import Actor
from app.shared.entity import _utc_now
from app.shared.files import IMAGE_TYPES, FileStorageProtocol, validate_upload
from app.shared.notifier import NotificationType, NotifierProtocol

SENSOR_METRICS = (
    HealthMetric.HEART_RATE,
    HealthMetric.ACTIVITY,
    HealthMetric.SLEEP,
    HealthMetric.TEMPERATURE,
)
_WORSENING_WORDS = ("worse", "worsening", "spreading", "increasing", "severe")


class SymptomParserPort(Protocol):
    """Symptom Parsing as this module needs it: owner text in, structured evidence out."""

    async def parse(self, text: str) -> SymptomEvidence: ...


@dataclass(frozen=True)
class HealthCheckInput:
    dog_id: str
    symptom_text: str = ""
    use_sensor_data: bool = False
    image: bytes | None = None
    image_content_type: str | None = None
    max_image_bytes: int = 0


@dataclass(frozen=True)
class HealthCheckOutcome:
    prediction: Prediction
    result: AssessmentResult
    dog_name: str


class RunHealthCheckUseCase:
    def __init__(
        self,
        predictions: PredictionRepositoryProtocol,
        readings: MetricReadingRepositoryProtocol,
        access: DogAccess,
        engine: FusionEngineProtocol,
        parser: SymptomParserPort,
        storage: FileStorageProtocol,
        notifier: NotifierProtocol,
    ):
        self._predictions = predictions
        self._readings = readings
        self._access = access
        self._engine = engine
        self._parser = parser
        self._storage = storage
        self._notifier = notifier

    async def execute(self, actor: Actor, data: HealthCheckInput) -> HealthCheckOutcome:
        dog = await self._access.owned(actor, data.dog_id)

        image_type = None
        if data.image:
            image_type = validate_upload(
                data.image, data.image_content_type, IMAGE_TYPES, data.max_image_bytes
            )
        text = data.symptom_text.strip()
        symptoms = await self._parser.parse(text) if text else None
        if symptoms and any(word in text.lower() for word in _WORSENING_WORDS):
            symptoms = SymptomEvidence(**{**asdict(symptoms), "worsening": True})
        sensors = await self._sensor_evidence(dog.id) if data.use_sensor_data else None
        if not (data.image or symptoms or sensors):
            raise NoEvidenceError()

        result = await self._engine.assess(
            FusionInput(
                dog=DogFacts(
                    name=dog.name,
                    breed=dog.breed,
                    age_years=dog.age_years,
                    allergies=tuple(dog.allergies),
                    special_notes=dog.special_notes,
                ),
                has_image=bool(data.image),
                symptoms=symptoms,
                sensors=sensors,
            )
        )
        previous = await self._predictions.latest_active(dog.id)
        image_file_id = await self._storage.save(data.image, image_type) if data.image else None
        prediction = await self._predictions.create(
            self._to_prediction(dog, result, symptoms, previous, image_file_id)
        )

        level = result.progression.risk_level
        if level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            await self._notifier.notify(
                dog.owner_id,
                NotificationType.AI_HEALTH_ALERT,
                f"AI Health Alert: {result.fusion.condition}",
                f"{dog.name}'s health check shows {level.value} risk. "
                f"{result.progression.recommendation}",
                dog_name=dog.name,
                action_label="View Prediction",
            )
        return HealthCheckOutcome(prediction=prediction, result=result, dog_name=dog.name)

    async def _sensor_evidence(self, dog_id: str) -> SensorEvidence | None:
        now = datetime.now(timezone.utc)
        since = history_start(MetricTimeRange.WEEKLY, now)
        points = []
        for metric in SENSOR_METRICS:
            readings = await self._readings.list_since(dog_id, metric, since)
            points += build_series(metric, MetricTimeRange.WEEKLY, readings, now).points
        if not points:
            return None
        abnormal = sum(1 for p in points if p.is_abnormal)
        return SensorEvidence(reading_count=len(points), abnormal_fraction=abnormal / len(points))

    @staticmethod
    def _to_prediction(
        dog: Dog,
        result: AssessmentResult,
        symptoms: SymptomEvidence | None,
        previous: Prediction | None,
        image_file_id: str | None,
    ) -> Prediction:
        fusion, progression = result.fusion, result.progression
        used = [m for m in fusion.modalities if m.available]
        if previous is None:
            comparison = f"This is {dog.name}'s first health check."
        else:
            change = progression.risk_percent - previous.combined_risk_percent
            direction = "up" if change > 0 else "down"
            since = previous.prediction_date.strftime("%d %b %Y")
            comparison = (
                f"Risk is unchanged since the last check on {since}."
                if abs(change) < 1
                else f"Risk is {direction} {abs(change):.0f} points since the last check on {since}."
            )
        return Prediction(
            dog_id=dog.id,
            title=fusion.condition,
            category=fusion.category,
            status=PredictionStatus.for_risk(progression.risk_level),
            combined_risk_percent=progression.risk_percent,
            confidence_percent=fusion.final_confidence_percent,
            model_version=result.model_version,
            affected_indicators=(
                [s.replace("_", " ").title() for s in symptoms.symptoms]
                if symptoms and symptoms.symptoms
                else progression.main_reasons
            ),
            recommended_next_step=progression.recommendation,
            model_contributions=[
                ModelContribution(f"{m.name} Model", m.contribution_percent) for m in used
            ],
            data_quality_note=(
                f"{len(used)} of {len(fusion.modalities)} evidence streams were available: "
                f"{', '.join(m.name for m in used)}."
            ),
            historical_comparison_note=comparison,
            image_file_id=image_file_id,
            assessment={
                "dog_name": dog.name,
                "fusion": asdict(fusion),
                "progression": {
                    **asdict(progression),
                    "risk_level": progression.risk_level.value,
                },
            },
        )


class ListPredictionsUseCase:
    def __init__(self, predictions: PredictionRepositoryProtocol, access: DogAccess):
        self._predictions = predictions
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> Sequence[Prediction]:
        dog = await self._access.readable(actor, dog_id)
        return await self._predictions.list_for_dog(dog.id)


class GetLatestPredictionUseCase:
    def __init__(self, predictions: PredictionRepositoryProtocol, access: DogAccess):
        self._predictions = predictions
        self._access = access

    async def execute(self, actor: Actor, dog_id: str) -> Prediction | None:
        dog = await self._access.readable(actor, dog_id)
        return await self._predictions.latest_active(dog.id)


class GetPredictionUseCase:
    def __init__(self, predictions: PredictionRepositoryProtocol, access: DogAccess):
        self._predictions = predictions
        self._access = access

    async def execute(self, actor: Actor, dog_id: str, prediction_id: str) -> Prediction:
        dog = await self._access.readable(actor, dog_id)
        prediction = await self._predictions.get_by_id(prediction_id)
        if prediction is None or prediction.dog_id != dog.id:
            raise PredictionNotFoundError()
        return prediction


class RecordPredictionOutcomeUseCase:
    def __init__(self, predictions: PredictionRepositoryProtocol, access: DogAccess):
        self._predictions = predictions
        self._access = access

    async def execute(
        self, actor: Actor, dog_id: str, prediction_id: str, outcome_note: str, resolved: bool
    ) -> Prediction:
        dog = await self._access.treatable(actor, dog_id)
        prediction = await self._predictions.get_by_id(prediction_id)
        if prediction is None or prediction.dog_id != dog.id:
            raise PredictionNotFoundError()
        prediction.outcome_note = outcome_note.strip()
        if resolved:
            prediction.status = PredictionStatus.RESOLVED
        prediction.updated_at = _utc_now()
        return await self._predictions.update(prediction)
