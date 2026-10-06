from typing import Protocol

from app.features.symptom_nlp.domain.entities import IntakeSession, SymptomParseResult


class NLPSymptomEngineProtocol(Protocol):
    async def parse(self, text: str) -> SymptomParseResult: ...

    def get_version(self) -> str: ...


class IntakeSessionRepositoryProtocol(Protocol):
    async def get(self, session_id: str) -> "IntakeSession | None": ...

    async def save(self, session: "IntakeSession") -> None: ...

    async def delete(self, session_id: str) -> bool: ...
