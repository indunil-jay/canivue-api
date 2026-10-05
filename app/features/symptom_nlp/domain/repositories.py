from typing import Protocol

from app.features.symptom_nlp.domain.entities import SymptomParseResult


class NLPSymptomEngineProtocol(Protocol):
    """Protocol for NLP symptom parsing and condition classification engines.
    
    Implementations must not expose heavy ML libraries (torch, transformers)
    to the domain or application layers.
    """

    async def parse(self, text: str) -> SymptomParseResult:
        """Parse raw symptom text into structured domain symptom evidence."""
        ...

    def get_version(self) -> str:
        """Return the version identifier of the loaded model checkpoint."""
        ...
