from typing import Protocol

from app.features.assessments.domain.value_objects.assessment_result import AssessmentResult
from app.features.assessments.domain.value_objects.fusion_input import FusionInput


class FusionEngineProtocol(Protocol):
    """Adaptive multimodal fusion plus seven-day progression risk for one Assessment."""

    async def assess(self, evidence: FusionInput) -> AssessmentResult: ...
