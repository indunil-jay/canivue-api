from app.features.assessments.application.interfaces.services.symptom_parser import (
    SymptomParserPort,
)
from app.features.assessments.domain.value_objects.symptom_evidence import SymptomEvidence
from app.features.symptom_nlp.application.commands.parse_symptom_text.parse_symptom_text_command import (
    ParseSymptomTextCommand,
)
from app.features.symptom_nlp.application.commands.parse_symptom_text.parse_symptom_text_command_handler import (
    ParseSymptomTextCommandHandler,
)


class SymptomNlpParser(SymptomParserPort):
    """Adapts the Symptom Parsing feature module to what an Assessment needs."""

    def __init__(self, parse_handler: ParseSymptomTextCommandHandler):
        self._parse = parse_handler

    async def parse(self, text: str) -> SymptomEvidence:
        parsed = await self._parse.handle(ParseSymptomTextCommand(text=text))
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
