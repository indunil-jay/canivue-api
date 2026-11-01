from dataclasses import dataclass

from app.features.assessments.domain.value_objects.modality_result import ModalityResult


@dataclass(frozen=True)
class FusionOutput:
    condition: str
    category: str
    final_confidence_percent: float
    severity_label: str
    modalities: list[ModalityResult]
    notes: list[str]
