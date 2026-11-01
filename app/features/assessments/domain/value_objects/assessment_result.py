from dataclasses import dataclass

from app.features.assessments.domain.value_objects.fusion_output import FusionOutput
from app.features.assessments.domain.value_objects.progression_output import ProgressionOutput


@dataclass(frozen=True)
class AssessmentResult:
    fusion: FusionOutput
    progression: ProgressionOutput
    model_version: str
