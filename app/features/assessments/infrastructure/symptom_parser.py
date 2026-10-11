from app.features.assessments.application.use_cases import SymptomParserPort
from app.features.assessments.domain.entities import SymptomEvidence
from app.features.symptom_nlp.application.dtos import ParseSymptomInputDTO
from app.features.symptom_nlp.application.use_cases import ParseSymptomTextUseCase


class SymptomNlpParser(SymptomParserPort):
    """Adapts the Symptom Parsing feature module to what an Assessment needs."""

    def __init__(self, parse_use_case: ParseSymptomTextUseCase):
        self._parse = parse_use_case

    async def parse(self, text: str) -> SymptomEvidence:
        parsed = await self._parse.execute(ParseSymptomInputDTO(text=text))
        triage = parsed.emergency_triage
        return SymptomEvidence(
            text=text,
            symptoms=tuple(parsed.symptoms),
            confidence=parsed.model_confidence,
            quality=parsed.text_quality_score,
            worsening=parsed.progression == "worsening",
            emergency_reason=triage.reason if triage.is_critical else None,
            emergency_recommendation=triage.recommendation if triage.is_critical else None,
        )
