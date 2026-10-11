from dataclasses import dataclass

from app.features.assessments.domain.value_objects.dog_facts import DogFacts
from app.features.assessments.domain.value_objects.sensor_evidence import SensorEvidence
from app.features.assessments.domain.value_objects.symptom_evidence import SymptomEvidence


@dataclass(frozen=True)
class FusionInput:
    dog: DogFacts
    has_image: bool = False
    symptoms: SymptomEvidence | None = None
    sensors: SensorEvidence | None = None
