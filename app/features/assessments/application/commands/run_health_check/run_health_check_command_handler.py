from dataclasses import asdict
from datetime import datetime, timezone

from app.features.assessments.application.commands.run_health_check.run_health_check_command import (
    RunHealthCheckCommand,
)
from app.features.assessments.application.dtos.health_check_outcome import HealthCheckOutcome
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.application.interfaces.services.fusion_engine import (
    FusionEngineProtocol,
)
from app.features.assessments.application.interfaces.services.symptom_parser import (
    SymptomParserPort,
)
from app.features.assessments.application.mappers.prediction_dto_mapper import PredictionDTOMapper
from app.features.assessments.domain.entities.prediction import Prediction
from app.features.assessments.domain.enums.prediction_status import PredictionStatus
from app.features.assessments.domain.enums.risk_level import RiskLevel
from app.features.assessments.domain.exceptions import NoEvidenceError
from app.features.assessments.domain.value_objects.assessment_result import AssessmentResult
from app.features.assessments.domain.value_objects.dog_facts import DogFacts
from app.features.assessments.domain.value_objects.fusion_input import FusionInput
from app.features.assessments.domain.value_objects.model_contribution import ModelContribution
from app.features.assessments.domain.value_objects.sensor_evidence import SensorEvidence
from app.features.assessments.domain.value_objects.symptom_evidence import SymptomEvidence
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.domain.entities.dog import Dog
from app.features.health_metrics.application.interfaces.repositories.metric_reading_repository import (
    MetricReadingRepositoryProtocol,
)
from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.domain.enums.metric_time_range import MetricTimeRange
from app.features.health_metrics.domain.services.build_series import build_series
from app.features.health_metrics.domain.services.history_start import history_start
from app.shared.files import IMAGE_TYPES, FileStorageProtocol, validate_upload
from app.shared.notifier import NotificationType, NotifierProtocol

SENSOR_METRICS = (
    HealthMetric.HEART_RATE,
    HealthMetric.ACTIVITY,
    HealthMetric.SLEEP,
    HealthMetric.TEMPERATURE,
)


_WORSENING_WORDS = ("worse", "worsening", "spreading", "increasing", "severe")


class RunHealthCheckCommandHandler:
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

    async def handle(self, command: RunHealthCheckCommand) -> HealthCheckOutcome:
        dog = await self._access.owned(command.actor, command.data.dog_id)

        image_type = None
        if command.data.image:
            image_type = validate_upload(
                command.data.image,
                command.data.image_content_type,
                IMAGE_TYPES,
                command.data.max_image_bytes,
            )
        text = command.data.symptom_text.strip()
        symptoms = await self._parser.parse(text) if text else None
        if symptoms and any(word in text.lower() for word in _WORSENING_WORDS):
            symptoms = SymptomEvidence(**{**asdict(symptoms), "worsening": True})
        sensors = await self._sensor_evidence(dog.id) if command.data.use_sensor_data else None
        if not (command.data.image or symptoms or sensors):
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
                has_image=bool(command.data.image),
                symptoms=symptoms,
                sensors=sensors,
            )
        )
        previous = await self._predictions.latest_active(dog.id)
        image_file_id = (
            await self._storage.save(command.data.image, image_type) if command.data.image else None
        )
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
        return HealthCheckOutcome(
            prediction=PredictionDTOMapper.to_output_dto(prediction),
            result=result,
            dog_name=dog.name,
        )

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
