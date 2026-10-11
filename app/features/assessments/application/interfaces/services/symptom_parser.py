from typing import Protocol

from app.features.assessments.domain.value_objects.symptom_evidence import SymptomEvidence


class SymptomParserPort(Protocol):
    """Symptom Parsing as this module needs it: owner text in, structured evidence out."""

    async def parse(self, text: str) -> SymptomEvidence: ...
