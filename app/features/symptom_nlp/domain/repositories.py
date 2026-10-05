from typing import Protocol

from app.features.symptom_nlp.domain.entities import IntakeSession, SymptomParseResult


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


class IntakeSessionRepositoryProtocol(Protocol):
    """Protocol for persisting and retrieving multi-turn intake sessions."""

    async def get(self, session_id: str) -> "IntakeSession | None":
        """Retrieve an intake session by unique identifier."""
        ...

    async def save(self, session: "IntakeSession") -> None:
        """Persist or update an intake session."""
        ...

    async def delete(self, session_id: str) -> bool:
        """Delete an intake session."""
        ...

