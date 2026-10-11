from typing import Protocol

from app.features.symptom_nlp.domain.value_objects.symptom_parse_result import SymptomParseResult


class NLPSymptomEngineProtocol(Protocol):
    async def parse(self, text: str) -> SymptomParseResult: ...

    def get_version(self) -> str: ...
